from google.cloud import bigquery
import pandas as pd
from config import Config

def execute_sql(sql_query: str) -> pd.DataFrame:
    """Executes a SQL query against BigQuery and returns a DataFrame."""
    try:
        # Relies on Application Default Credentials (ADC)
        client = bigquery.Client(project=Config.GCP_PROJECT_ID)
        query_job = client.query(sql_query)
        df = query_job.to_dataframe()
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})