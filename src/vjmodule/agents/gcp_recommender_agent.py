"""GCP Recommender agent — data-driven optimisation using real billing + Recommender API.

Never hallucinate. Every recommendation is anchored to actual spend from the
BigQuery billing export. The GCP Recommender API provides supplementary signals.
"""
from __future__ import annotations

import json
from typing import Generator

import pandas as pd

from config import GCPConfig
from vjmodule.connectors.gcp_recommender import get_recommendations
from vjmodule.connectors.gcp_billing import get_cost_summary


def stream_recommendations(
    question: str,
    project_id: str,
    days: int = 30,
) -> Generator[str, None, None]:
    """Yield streaming, data-grounded recommendation analysis for *project_id*."""
    if not project_id:
        yield "⚠️ No GCP project selected. Please choose a project from the dropdown above."
        return

    yield f"_Fetching real billing data for **`{project_id}`** (last {days} days)…_\n\n"

    try:
        # ── 1. Actual billing data ────────────────────────────────────────────
        summary      = get_cost_summary(project_id, days=days)
        cost_df      = summary["cost_data"]
        billing_info = summary["billing_info"]
        services     = summary["enabled_services"]

        has_cost = (
            not cost_df.empty
            and "status" not in cost_df.columns
            and "error"  not in cost_df.columns
        )

        # ── 2. Recommender API signals ────────────────────────────────────────
        yield "_Querying GCP Recommender API…_\n\n"
        recs        = get_recommendations(project_id)
        has_api_rec = bool(recs) and "error" not in recs[0]

        # ── 3. Yield real cost table so the user sees hard numbers first ──────
        if has_cost:
            currency    = cost_df["currency"].iloc[0] if "currency" in cost_df.columns else "USD"
            total_spend = cost_df["total_cost"].sum()

            svc_totals = (
                cost_df.groupby("service")["total_cost"]
                .sum()
                .reset_index()
                .sort_values("total_cost", ascending=False)
            )
            svc_totals["pct"] = (svc_totals["total_cost"] / total_spend * 100).round(1)

            top_skus = (
                cost_df.groupby(["service", "sku"])["total_cost"]
                .sum()
                .reset_index()
                .sort_values("total_cost", ascending=False)
                .head(40)
            )

            # Monthly trend (if data spans multiple months)
            trend_lines = ""
            if "month" in cost_df.columns and cost_df["month"].nunique() > 1:
                monthly = (
                    cost_df.groupby("month")["total_cost"]
                    .sum()
                    .reset_index()
                    .sort_values("month")
                )
                trend_lines = "\n\n**Monthly Spend:**\n\n"
                trend_lines += "| Month | Spend |\n|---|---|\n"
                trend_lines += "".join(
                    f"| {r['month']} | {currency} {r['total_cost']:,.2f} |\n"
                    for _, r in monthly.iterrows()
                )

            yield (
                f"## 💰 Actual Cost Breakdown — `{project_id}`\n\n"
                f"**Period:** Last {days} days &nbsp;|&nbsp; "
                f"**Total Spend:** `{currency} {total_spend:,.2f}`\n\n"
                "| Service | Spend | % of Total |\n|---|---|---|\n"
                + "".join(
                    f"| {r['service']} | {currency} {r['total_cost']:,.2f} | {r['pct']}% |\n"
                    for _, r in svc_totals.iterrows()
                )
                + (trend_lines or "")
                + "\n\n---\n\n"
            )

            if has_api_rec:
                yield f"_GCP Recommender API: **{len(recs)} active signal(s)** found. Running AI analysis…_\n\n"
            else:
                yield "_GCP Recommender API: no active signals. Analysing billing data only…_\n\n"

            # ── Build full LLM context (only real data, no guessing) ──────────
            billing_context = f"""=== ACTUAL BILLING DATA (last {days} days) ===
Project: {project_id}
Total spend: {currency} {total_spend:,.2f}

Cost by Service (sorted by spend):
{svc_totals[['service','total_cost','pct']].to_string(index=False)}

Top {len(top_skus)} Cost Line Items (Service + SKU):
{top_skus.to_string(index=False)}

Enabled services count: {summary['enabled_services_count']}
"""

        else:
            billing_context = (
                f"No billing export data available for project {project_id}. "
                "Recommendations can only be based on the Recommender API signals below."
            )
            yield (
                "⚠️ **No billing export data found** — recommendations limited to "
                "GCP Recommender API signals only.\n\n---\n\n"
            )
            if has_api_rec:
                yield f"_GCP Recommender API: **{len(recs)} active signal(s)**. Analysing…_\n\n"

        api_context = (
            f"=== GCP RECOMMENDER API SIGNALS ({len(recs)} active) ===\n"
            + json.dumps(recs, indent=2)
            if has_api_rec
            else "=== GCP RECOMMENDER API === No active recommendations returned."
        )

        # ── 4. Strict grounded prompt ─────────────────────────────────────────
        prompt = f"""You are a senior GCP cost optimisation engineer performing a deep financial analysis.

ABSOLUTE RULES — NEVER BREAK THESE:
1. Base EVERY recommendation on the data provided below. Do NOT invent, assume, or add generic advice.
2. Only recommend changes for services that appear in the billing data with actual spend figures.
3. Every recommendation row MUST include the real current monthly spend for that service (from the data).
4. When estimating savings, explain the reasoning using actual SKU names and spend proportions from the data — never pull numbers from general knowledge.
5. Always evaluate INDIRECT USAGE before recommending deletion or downsizing. A resource may look idle but serve another purpose (e.g., a Cloud Storage bucket may be a Logging export sink, a Pub/Sub topic may be driven by a Cloud Function, a VM may serve as a NAT gateway). Flag these risks explicitly.
6. If a service appears in billing data but its SKU names suggest reserved capacity, licensing, or committed use, note that reducing it may not save proportionally.
7. If the billing data is unavailable or a service has 0 spend in the data, do NOT make up recommendations for it.

{billing_context}

{api_context}

User question: {question}

Respond in exactly these sections:

## 🔍 What's Actually Driving Your Costs
Analyse the top cost drivers line by line. Use real numbers from the data. Explain in plain English what each service/SKU charge means (e.g., "Compute Engine N2 Instance Core running in us-central1 means you're paying for vCPUs on a live VM"). Identify patterns — e.g., is one service dominating? Is there a spike in a particular month?

## 🎯 Specific Recommendations (Evidence-Based Only)
For each recommendation, fill out this table row:
| Service | Current Spend ({currency if has_cost else 'USD'}) | Recommended Action | Est. Saving | Risk | Indirect Usage to Verify |
|---|---|---|---|---|---|
Only include rows for services that appear in the billing data above. Risk = LOW / MEDIUM / HIGH.

## ⚠️ Indirect Usage Warnings
For each recommendation above, explain step by step what to check before making the change. E.g.:
- "Before deleting this Cloud Storage bucket: check Logging → Log Router for sinks pointing to this bucket; check Backup configs; check any Cloud Functions with Storage triggers."
- "Before rightsizing this VM: check if it has static IP used by other services; check Firewall rules referencing it by tag; check if it runs a scheduled job."

## 📉 Highest-ROI Safe Changes
Top 3 changes (from your recommendations above) with the best savings-to-risk ratio. For each: current spend, action, estimated saving %, and why it is safe.

## 🚫 Watch List — Do Not Touch Yet
List any services from the billing data that look expensive but show patterns suggesting important indirect usage. Explain the pattern and what to investigate first.

Bold all monetary amounts. Use real numbers throughout. If you cannot make a recommendation with evidence, say so explicitly rather than guessing."""

        for chunk in GCPConfig.get_llm().stream(prompt):
            if chunk.content:
                yield chunk.content

    except Exception as exc:
        yield f"\n\n❌ **Error during analysis:** {exc}"
