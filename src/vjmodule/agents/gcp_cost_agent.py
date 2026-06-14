"""GCP Cost Analyser agent — streams actual billing data per service.

Uses the gcp_billing connector to fetch real billing data and displays
it as formatted tables without LLM recommendations.
"""
from __future__ import annotations

from typing import Generator

from connectors.gcp_billing import get_cost_summary


def stream_cost_analysis(
    question: str,
    project_id: str,
    days: int = 30,
) -> Generator[str, None, None]:
    """Yield actual billing cost data per service for *project_id*."""
    if not project_id:
        yield "⚠️ No GCP project selected. Please choose a project from the dropdown above."
        return

    yield f"_Fetching billing data for **`{project_id}`** (last {days} days)…_\n\n"

    try:
        summary   = get_cost_summary(project_id, days=days)
        billing   = summary["billing_info"]
        cost_df   = summary["cost_data"]
        svc_count = summary["enabled_services_count"]

        # ── Header ───────────────────────────────────────────────────────────
        yield (
            f"## 💰 GCP Billing — `{project_id}`\n\n"
            f"| | |\n|---|---|\n"
            f"| **Period** | Last {days} days |\n"
            f"| **Billing enabled** | {billing.get('billing_enabled', 'unknown')} |\n"
            f"| **Billing account** | `{billing.get('billing_account') or 'N/A'}` |\n"
            f"| **Enabled services** | {svc_count} |\n\n"
        )

        # ── No billing export configured ─────────────────────────────────────
        if "status" in cost_df.columns:
            services = summary["enabled_services"]
            svc_list = "\n".join(
                f"| {i+1} | {s.get('title', s.get('name', ''))} | `{s.get('name', '')}` |"
                for i, s in enumerate(services[:30])
            )
            yield (
                "⚠️ **Billing export not configured — no cost data available yet.**\n\n"
                "> To get per-service costs, enable BigQuery billing export (free):\n"
                "> **GCP Console → Billing → Billing Export → BigQuery export → Edit settings**\n"
                "> Data starts appearing within a few hours.\n\n"
                "---\n\n"
                "### 🟢 Currently Enabled Services (what may be generating cost)\n\n"
                f"Billing account: `{billing.get('billing_account') or 'N/A'}`\n\n"
            )
            if services:
                yield (
                    "| # | Service | API Name |\n|---|---|---|\n"
                    + svc_list
                    + "\n"
                )
            else:
                yield "_No enabled services found._\n"
            return

        if "error" in cost_df.columns:
            yield f"❌ **Error fetching billing data:** {cost_df['error'].iloc[0]}"
            return

        # ── Per-service cost summary ─────────────────────────────────────────
        total = cost_df["total_cost"].sum()
        currency = cost_df["currency"].iloc[0] if "currency" in cost_df.columns else "USD"

        svc_summary = (
            cost_df.groupby("service")["total_cost"]
            .sum()
            .reset_index()
            .rename(columns={"total_cost": "cost"})
            .sort_values("cost", ascending=False)
        )
        svc_summary["% of total"] = (svc_summary["cost"] / total * 100).round(1)

        yield f"### 📊 Cost by Service\n\n**Total spend:** `{currency} {total:,.2f}`\n\n"

        rows = "| Service | Cost ({}) | % of Total |\n|---|---|---|\n".format(currency)
        for _, row in svc_summary.iterrows():
            rows += f"| {row['service']} | {row['cost']:,.4f} | {row['% of total']}% |\n"
        rows += f"| **TOTAL** | **{total:,.4f}** | **100%** |\n"
        yield rows

        # ── Per-month breakdown (if multiple months) ─────────────────────────
        if "month" in cost_df.columns and cost_df["month"].nunique() > 1:
            monthly = (
                cost_df.groupby("month")["total_cost"]
                .sum()
                .reset_index()
                .sort_values("month")
            )
            yield f"\n### 📅 Monthly Spend\n\n"
            month_rows = f"| Month | Cost ({currency}) |\n|---|---|\n"
            for _, row in monthly.iterrows():
                month_rows += f"| {row['month']} | {row['total_cost']:,.4f} |\n"
            yield month_rows

        # ── SKU-level breakdown ──────────────────────────────────────────────
        yield f"\n### 🔍 SKU-Level Breakdown (Top 50)\n\n"

        sku_cols = ["service", "sku", "total_cost"]
        if "month" in cost_df.columns:
            sku_cols.insert(2, "month")
        if "currency" in cost_df.columns:
            sku_cols.append("currency")

        top_skus = cost_df[sku_cols].sort_values("total_cost", ascending=False).head(50)

        header_cols = ["Service", "SKU"]
        if "month" in cost_df.columns:
            header_cols.append("Month")
        header_cols += [f"Cost ({currency})"]

        sku_rows = "| " + " | ".join(header_cols) + " |\n"
        sku_rows += "|" + "|".join(["---"] * len(header_cols)) + "|\n"
        for _, row in top_skus.iterrows():
            parts = [str(row["service"]), str(row["sku"])]
            if "month" in cost_df.columns:
                parts.append(str(row["month"]))
            parts.append(f"{row['total_cost']:,.4f}")
            sku_rows += "| " + " | ".join(parts) + " |\n"
        yield sku_rows

    except Exception as exc:
        yield f"\n\n❌ **Error during cost analysis:** {exc}"
