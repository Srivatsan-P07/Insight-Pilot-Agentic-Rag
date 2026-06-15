from __future__ import annotations

from typing import Generator

from config import Config
from vjmodule.connectors import dataplex_catalog


def stream_sql_analysis(question: str) -> Generator[str, None, None]:
    """Yield streaming SQL generation, execution, and LLM analysis."""
    from vjmodule.connectors.bigquery import execute_sql

    yield "_Fetching metadata and generating SQL..._\n\n"
    try:
        sql = generate_sql(question)
        yield f"**Generated SQL:**\n```sql\n{sql}\n```\n\n_Executing..._\n\n"

        df = execute_sql(sql)

        if "error" in df.columns:
            yield f"⚠️ **Query error:**\n```\n{df['error'].iloc[0]}\n```"
            return

        if df.empty:
            yield "Query returned **no results**."
            return

        yield f"**Results — {len(df)} row(s):**\n\n{df.head(100).to_markdown(index=False)}\n\n"

        analysis_prompt = f"""You are a data analyst. The user asked: \"{question}\"

SQL used:
```sql
{sql}
```

Results ({len(df)} rows, first 50 shown):
{df.head(50).to_string(index=False)}

Provide:
## 📊 Key Findings
## 📈 Trends & Patterns
## 💼 Business Insights
## 🔍 Suggested Follow-ups

Be concise and use markdown.
"""
        for chunk in Config.llm.stream(analysis_prompt):
            if chunk.content:
                yield chunk.content

    except Exception as exc:
        yield f"\n\n\u274c **Error:** {exc}"


def generate_sql(question: str, knowledge: str = None) -> str:
    """Uses Gemini and Dataplex metadata to write a BigQuery SQL statement."""
    dataplex_catalog.extract_and_save_dataplex_metadata()
    metadata = dataplex_catalog.load_local_dataplex_metadata()

    if knowledge:
        metadata += f"\n\nAdditional knowledge provided by user: {knowledge}"
    
    prompt = f"""
    You are a BigQuery SQL expert. Write a SQL query to answer the user's question.
    bigquery expects fully qualified table names in the format `dataset.table`.
    Use ONLY the tables, columns, and descriptions provided in this Dataplex metadata schema.:
    
    {metadata}
    
    Question: {question}
    
    Return ONLY the raw SQL query. Do not include markdown formatting like ```sql.
    """
    
    sql = Config.llm.invoke(prompt).content.strip()
    # Clean up standard markdown code blocks if the LLM adds them
    return sql.replace("```sql", "").replace("```", "").strip()