"""GCP Recommender connector — fetches active recommendations via ADC.

Scans multiple regions and recommender types so callers get a complete
picture of savings opportunities without any manual configuration.
"""
from __future__ import annotations

import concurrent.futures
from typing import Optional

# ── Recommender catalogue ────────────────────────────────────────────────────

RECOMMENDER_CATALOGUE: dict[str, str] = {
    "idle_vm":              "google.compute.instance.IdleResourceRecommender",
    "vm_rightsizing":       "google.compute.instance.MachineTypeRecommender",
    "disk_idle":            "google.compute.disk.IdleResourceRecommender",
    "snapshot_idle":        "google.compute.image.IdleResourceRecommender",
    "spend_commitment":     "google.compute.commitment.UsageCommitmentRecommender",
    "bigquery_slots":       "google.bigquery.capacityCommitments.Recommender",
    "iam_policy":           "google.iam.policy.Recommender",
    "cloudsql_idle":        "google.cloudsql.instance.IdleRecommender",
    "cloudsql_overprovisioned": "google.cloudsql.instance.OverprovisionedRecommender",
    "gke_node_pool":        "google.container.DiagnosisRecommender",
}

REGIONS_TO_SCAN: list[str] = [
    "global",
    "us-central1",
    "us-east1",
    "us-west1",
    "us-west2",
    "europe-west1",
    "europe-west4",
    "asia-east1",
    "asia-southeast1",
]

_PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "PRIORITY_UNSPECIFIED": 4}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _format_impact(impact) -> str:
    if not impact:
        return "Unknown"
    category = impact.category.name if hasattr(impact, "category") else "UNKNOWN"
    try:
        cp = impact.cost_projection
        if cp and cp.cost:
            amount = cp.cost.units + cp.cost.nanos / 1e9
            currency = cp.cost.currency_code
            label = "Saves" if amount < 0 else "Costs extra"
            return f"{category} — {label} {currency} {abs(amount):.2f}/month"
    except Exception:
        pass
    return category


# ── Main function ────────────────────────────────────────────────────────────

def get_recommendations(
    project_id: str,
    recommender_ids: Optional[list[str]] = None,
    regions: Optional[list[str]] = None,
) -> list[dict]:
    """
    Return all ACTIVE recommendations for *project_id*.

    Runs all region × recommender combinations in parallel (max 20 threads)
    so the full scan completes in seconds instead of minutes.
    Silently skips combinations that return permission errors or are unavailable.
    """
    try:
        from google.cloud import recommender_v1
        client = recommender_v1.RecommenderClient()
    except Exception as exc:
        return [{"error": f"Recommender API unavailable: {exc}"}]

    ids  = recommender_ids or list(RECOMMENDER_CATALOGUE.values())
    locs = regions or REGIONS_TO_SCAN

    def _fetch(loc: str, rid: str) -> list[dict]:
        chunk: list[dict] = []
        try:
            parent = f"projects/{project_id}/locations/{loc}/recommenders/{rid}"
            for rec in client.list_recommendations(
                parent=parent,
                filter='stateInfo.state="ACTIVE"',
            ):
                chunk.append(
                    {
                        "name":        rec.name,
                        "description": rec.description,
                        "recommender": rid.split(".")[-1],
                        "location":    loc,
                        "priority":    getattr(rec, "priority", None) and rec.priority.name or "P4",
                        "impact":      _format_impact(rec.primary_impact),
                        "state":       rec.state_info.state.name,
                    }
                )
        except Exception:
            pass
        return chunk

    results: list[dict] = []
    pairs = [(loc, rid) for loc in locs for rid in ids]

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(_fetch, loc, rid): (loc, rid) for loc, rid in pairs}
        for future in concurrent.futures.as_completed(futures, timeout=60):
            try:
                results.extend(future.result())
            except Exception:
                pass

    results.sort(key=lambda r: _PRIORITY_ORDER.get(r.get("priority", "P4"), 5))
    return results
