from __future__ import annotations

from config import Config

_VALID_AGENTS = {
    "gcp_cost", "gcp_recommender", "github", "code_optimizer", "docs", "sql"
}


def route_to_agent(question: str) -> str:
    """
    Route *question* to the most appropriate agent ID.

    Returns one of: gcp_cost | gcp_recommender | github | code_optimizer | docs | sql
    """
    prompt = f"""You are a routing assistant for an AI platform with these specialist agents:
- gcp_cost         : GCP billing, cost analysis, spending, invoices, budgets
- gcp_recommender  : GCP optimisation, rightsizing, idle resources, recommendations
- github           : GitHub pull requests, commits, code review, repositories
- code_optimizer   : Analysing source code for GCP cost inefficiencies
- docs             : Confluence documentation search, process definitions, how-to guides
- sql              : BigQuery SQL queries, data analysis, metrics, reports

Question: {question}

Return ONLY the agent ID. No explanation."""

    try:
        agent_id = Config.llm.invoke(prompt).content.strip().lower().strip('"\' ')
        return agent_id if agent_id in _VALID_AGENTS else "docs"
    except Exception:
        return "docs"


def route_question(question: str) -> str:
    """Determines if the question needs BIGQUERY, CONFLUENCE, or BOTH."""
    
    prompt = f"""
    You are a routing assistant. Analyze the user's question and determine the data source needed.
    - If it asks for metrics, numbers, tables, or database data, return "BIGQUERY".
    - If it asks for definitions, process documentation, or 'how to', return "CONFLUENCE".
    - If it requires both, return "BOTH".
    - If it cannot be determined, return "UNKNOWN".
    
    Question: {question}
    
    Return ONLY the category word.
    """
    
    response = Config.llm.invoke(prompt)
    return response.content.strip()