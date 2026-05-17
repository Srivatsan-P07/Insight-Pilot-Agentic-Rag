from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from typing import List, Dict, Any, Optional
import pandas as pd
from config import AppLogger

logger = AppLogger.setup()

class BigQueryConnector:
    """A connector class for interacting with Google BigQuery."""
    
    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """
        Initialize BigQuery connector.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON file (optional)
        """
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        logger.app(f"Initialized BigQueryConnector for project: {project_id}")
    
    def query(self, sql: str, job_config: Optional[bigquery.QueryJobConfig] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.
        
        Args:
            sql: SQL query string
            job_config: Optional QueryJobConfig
            
        Returns:
            DataFrame with query results
        """
        try:
            logger.debug(f"Executing SQL query: {sql}")
            query_job = self.client.query(sql, job_config=job_config)
            df = query_job.to_dataframe()
            logger.app(f"Query executed successfully. Returned {len(df)} rows.")
            return df
        except GoogleCloudError as e:
            logger.error(f"BigQuery query failed: {str(e)}")
            raise Exception(f"BigQuery query failed: {str(e)}")
    
    def get_table(self, table_id: str) -> bigquery.Table:
        """Get table metadata."""
        logger.debug(f"Fetching metadata for table: {table_id}")
        return self.client.get_table(table_id)
    
    def close(self) -> None:
        """Close the BigQuery client."""
        self.client.close()
        logger.app("BigQuery client closed.")