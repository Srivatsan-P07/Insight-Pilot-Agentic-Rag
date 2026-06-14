"""GCP Cloud Billing connector — ADC-based billing data retrieval.

Supports:
  - Listing billing accounts and project billing info
  - Listing enabled APIs via Service Usage
  - Querying BigQuery billing export (standard GCP cost export)
  - Smart auto-discovery: scans ALL datasets, scores tables/views by name
    pattern, handles custom views and flat schemas
"""
from __future__ import annotations

import re
from typing import Optional
import concurrent.futures

import pandas as pd


# ── Billing account helpers ──────────────────────────────────────────────────

def get_billing_accounts() -> list[dict]:
    """Return all Cloud Billing accounts accessible to the authenticated user."""
    try:
        from google.cloud import billing_v1

        client = billing_v1.CloudBillingClient()
        return [
            {
                "name": a.name,
                "display_name": a.display_name,
                "open": a.open_,
                "master_billing_account": a.master_billing_account_name,
            }
            for a in client.list_billing_accounts()
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


def get_project_billing_info(project_id: str) -> dict:
    """Return the billing account linked to *project_id*."""
    try:
        from google.cloud import billing_v1

        client = billing_v1.CloudBillingClient()
        info = client.get_project_billing_info(name=f"projects/{project_id}")
        return {
            "billing_account": info.billing_account_name,
            "billing_enabled": info.billing_enabled,
        }
    except Exception as exc:
        return {"billing_account": None, "billing_enabled": False, "error": str(exc)}


# ── Service Usage ────────────────────────────────────────────────────────────

def get_enabled_services(project_id: str) -> list[dict]:
    """List all enabled APIs/services for *project_id* via Service Usage API.

    Wrapped in a 15-second timeout so a slow or unresponsive Discovery endpoint
    never blocks the cost analysis stream indefinitely.
    """
    def _fetch() -> list[dict]:
        import google.auth
        import googleapiclient.discovery

        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        svc = googleapiclient.discovery.build(
            "serviceusage", "v1", credentials=creds, cache_discovery=False
        )
        services: list[dict] = []
        request = svc.services().list(
            parent=f"projects/{project_id}",
            filter="state:ENABLED",
            pageSize=200,
        )
        while request:
            resp = request.execute()
            for s in resp.get("services", []):
                cfg = s.get("config", {})
                services.append(
                    {
                        "name": cfg.get("name", ""),
                        "title": cfg.get("title", cfg.get("name", "")),
                    }
                )
            request = svc.services().list_next(request, resp)
        return services

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_fetch)
            return future.result(timeout=15)
    except concurrent.futures.TimeoutError:
        return [{"error": "Service Usage API timed out after 15 s"}]
    except Exception as exc:
        return [{"error": str(exc)}]


# ── BigQuery billing export ──────────────────────────────────────────────────

# Scoring rules for table/view names — first match wins (highest score = best candidate).
_TABLE_SCORE_RULES: list[tuple[int, re.Pattern]] = [
    (100, re.compile(r"gcp_billing_export_resource_v1_",  re.I)),
    (90,  re.compile(r"gcp_billing_export_v1_",           re.I)),
    (70,  re.compile(r"gcp_billing_export",               re.I)),
    (50,  re.compile(r"billing.{0,15}export|export.{0,15}billing", re.I)),
    (40,  re.compile(r"billing.{0,15}cost|cost.{0,15}billing",     re.I)),
    (30,  re.compile(r"billing",                          re.I)),
    (20,  re.compile(r"\bcost\b",                         re.I)),
]

# Dataset name keywords that suggest it may host billing data.
_BILLING_DS_KEYWORDS = frozenset(["billing", "cost", "spend", "finance", "charges"])

# BigQuery multi-region / region prefixes for INFORMATION_SCHEMA queries.
_BQ_REGIONS = ["region-us", "region-eu", "us", "eu"]


def _score_table(dataset_id: str, table_id: str) -> int:
    """Return a relevance score for how likely this table contains billing data."""
    for pts, pat in _TABLE_SCORE_RULES:
        if pat.search(table_id):
            score = pts
            break
    else:
        score = 0
    # Bonus when the dataset name itself signals billing data.
    if any(kw in dataset_id.lower() for kw in _BILLING_DS_KEYWORDS):
        score += 10
    return score


def _discover_billing_table(bq, project_id: str) -> Optional[tuple[str, str]]:
    """
    Scan *project_id* and return ``(dataset_ref, table_id)`` for the
    best-matching billing export table or view, or ``None``.

    Strategy (fastest → most thorough):
    1. INFORMATION_SCHEMA — one query per region covers ALL datasets at once.
       Filters on table names OR dataset names containing 'billing' or 'cost'.
    2. Fallback dataset scan — lists every dataset; scores each table/view.
       Billing-keyword datasets are explored first.
    """
    from google.cloud import bigquery

    best_score: int = 0
    best: Optional[tuple[str, str]] = None

    def _update(ds_ref: str, tbl_id: str, ds_id: str) -> None:
        nonlocal best_score, best
        s = _score_table(ds_id, tbl_id)
        if s > best_score:
            best_score, best = s, (ds_ref, tbl_id)

    # ── 1. INFORMATION_SCHEMA (single query covers every dataset) ────────────
    for region in _BQ_REGIONS:
        try:
            sql = f"""
                SELECT table_schema, table_name
                FROM `{project_id}.{region}.INFORMATION_SCHEMA.TABLES`
                WHERE
                    LOWER(table_name)   LIKE '%billing%'
                    OR LOWER(table_name)   LIKE '%cost%'
                    OR LOWER(table_schema) LIKE '%billing%'
                    OR LOWER(table_schema) LIKE '%cost%'
                LIMIT 100
            """
            rows = list(
                bq.query(
                    sql,
                    job_config=bigquery.QueryJobConfig(job_timeout_ms=10_000),
                ).result()
            )
            for row in rows:
                ds_ref = f"{project_id}.{row.table_schema}"
                _update(ds_ref, row.table_name, row.table_schema)
            if rows:
                break  # found results in this region — no need to try others
        except Exception:
            continue

    if best_score >= 20:
        return best

    # ── 2. Full dataset scan fallback ────────────────────────────────────────
    try:
        all_ds = list(bq.list_datasets(project=project_id))
    except Exception:
        all_ds = []

    # Billing-hint datasets first for faster discovery.
    def _ds_priority(ds) -> int:
        return 0 if any(kw in ds.dataset_id.lower() for kw in _BILLING_DS_KEYWORDS) else 1

    for ds in sorted(all_ds, key=_ds_priority):
        ds_ref = f"{project_id}.{ds.dataset_id}"
        try:
            for tbl in bq.list_tables(ds_ref, max_results=300, timeout=8):
                _update(ds_ref, tbl.table_id, ds.dataset_id)
        except Exception:
            continue

    return best if best_score >= 20 else None


def get_accessible_projects() -> list[str]:
    """Return project IDs accessible to the authenticated user (up to 50)."""
    try:
        from google.cloud import resourcemanager_v3

        client = resourcemanager_v3.ProjectsClient()
        return [
            p.project_id
            for p in client.search_projects(query="state:ACTIVE")
            if p.state.name == "ACTIVE"
        ][:50]
    except Exception:
        return []


def query_billing_export(
    project_id: str,
    billing_export_dataset: Optional[str] = None,
    days: int = 30,
    extra_search_projects: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Query the BigQuery billing export for cost breakdown.

    Discovery order:
    1. Explicitly provided *billing_export_dataset*.
    2. Smart discovery in *project_id*: INFORMATION_SCHEMA + full dataset scan,
       scored by table/dataset name patterns (billing, cost, export, etc.).
    3. Cross-project search in *extra_search_projects* — billing export may live
       in a dedicated finance/billing project.

    Query strategy per discovered table:
    - Exact table/view name used directly (no wildcards needed).
    - First attempts the standard nested GCP export schema
      (service.description, sku.description, project.id).
    - Falls back to a flat-column schema for custom views where columns have
      been aliased (service_description, sku_description, project_id, etc.).

    All queries filter by project so costs shown always belong to *project_id*.
    """
    from google.cloud import bigquery

    bq = bigquery.Client(project=project_id)

    # ── SQL templates ────────────────────────────────────────────────────────

    # Standard GCP billing export schema (nested RECORD fields).
    _NESTED_SQL = """
SELECT
    service.description             AS service,
    sku.description                 AS sku,
    ROUND(SUM(cost), 4)             AS total_cost,
    currency,
    FORMAT_DATE('%Y-%m', usage_start_time) AS month
FROM {tref}
WHERE
    DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    AND project.id = @project_id
GROUP BY service, sku, currency, month
ORDER BY total_cost DESC
LIMIT 500
"""

    # Flat schema — for custom views / materialized views that flatten columns.
    _FLAT_SQL = """
SELECT
    COALESCE(
        CAST(service_description AS STRING),
        CAST(service AS STRING),
        'Unknown'
    )                                           AS service,
    COALESCE(
        CAST(sku_description AS STRING),
        CAST(sku AS STRING),
        ''
    )                                           AS sku,
    ROUND(SUM(COALESCE(cost, 0)), 4)            AS total_cost,
    COALESCE(currency, 'USD')                   AS currency,
    FORMAT_DATE('%Y-%m', usage_start_time)      AS month
FROM {tref}
WHERE
    DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
GROUP BY service, sku, currency, month
ORDER BY total_cost DESC
LIMIT 500
"""

    def _exec(sql: str, tref: str) -> Optional[pd.DataFrame]:
        try:
            job_config = bigquery.QueryJobConfig(
                job_timeout_ms=25_000,
                query_parameters=[
                    bigquery.ScalarQueryParameter("project_id", "STRING", project_id)
                ],
            )
            df = bq.query(
                sql.format(tref=tref, days=days),
                job_config=job_config,
            ).to_dataframe()
            return df if not df.empty else None
        except Exception:
            return None

    def _query_exact(dataset: str, table_id: str) -> Optional[pd.DataFrame]:
        """Query a specific table or view by exact name, trying both schemas."""
        if not table_id:
            return None
        tref = f"`{dataset}.{table_id}`"
        df = _exec(_NESTED_SQL, tref)
        if df is not None:
            return df
        return _exec(_FLAT_SQL, tref)

    def _query_wildcards(dataset: str) -> Optional[pd.DataFrame]:
        """Fallback: try standard GCP wildcard table patterns."""
        for pattern in (
            f"`{dataset}.gcp_billing_export_v1_*`",
            f"`{dataset}.gcp_billing_export_resource_v1_*`",
        ):
            df = _exec(_NESTED_SQL, pattern)
            if df is not None:
                return df
        return None

    def _query_project(pid: str) -> Optional[pd.DataFrame]:
        """Run full discovery + query for a given project."""
        # Explicit dataset hint (only used for the primary project_id).
        if pid == project_id and billing_export_dataset:
            result = _discover_billing_table(bq, pid)
            # Try the hinted dataset first
            df = _query_wildcards(billing_export_dataset)
            if df is None and result is not None and result[0].endswith(
                    billing_export_dataset.split(".")[-1]):
                df = _query_exact(billing_export_dataset, result[1])
            if df is not None:
                return df

        result = _discover_billing_table(bq, pid)
        if result:
            ds_ref, tbl_id = result
            df = _query_exact(ds_ref, tbl_id)
            if df is not None:
                return df
            # Exact query failed (schema mismatch) — try wildcards in same dataset.
            df = _query_wildcards(ds_ref)
            if df is not None:
                return df
        return None

    # ── Step 1 & 2: primary project ──────────────────────────────────────────
    df = _query_project(project_id)
    if df is not None:
        return df

    # ── Step 3: cross-project search ─────────────────────────────────────────
    for other_pid in (extra_search_projects or [])[:8]:
        if other_pid == project_id:
            continue
        df = _query_project(other_pid)
        if df is not None:
            return df

    return pd.DataFrame(
        {
            "status": [
                "No BigQuery billing export found. "
                "Enable it at GCP Console → Billing → Billing Export → BigQuery export."
            ]
        }
    )


# ── Unified summary ──────────────────────────────────────────────────────────

def get_cost_summary(project_id: str, days: int = 30) -> dict:
    """Fetch all billing context for *project_id* in one call.

    Automatically searches for the billing export across all accessible projects
    so the export doesn't need to live in the same project being analysed.
    """
    billing_info = get_project_billing_info(project_id)
    services = get_enabled_services(project_id)

    try:
        all_projects = get_accessible_projects()
    except Exception:
        all_projects = []

    cost_df = query_billing_export(
        project_id,
        days=days,
        extra_search_projects=all_projects,
    )

    return {
        "project_id": project_id,
        "billing_info": billing_info,
        "enabled_services_count": len([s for s in services if "error" not in s]),
        "enabled_services": [s for s in services if "error" not in s],
        "cost_data": cost_df,
        "days_analyzed": days,
    }
