from config import AppLogger
from typing import Optional
from google.cloud import datacatalog_v1
from google.cloud.datacatalog_v1.types import Schema
from google.api_core.exceptions import NotFound, GoogleAPICallError
from collections import defaultdict
from utils import multi_thread

logger = AppLogger.setup()


class DataplexConnector:
    """
    Handles connection of schemas from Google Cloud Data Catalog.
    Supports fetching updated schemas and deleting schemas for removed tables.
    """

    def __init__(self, project_id: str):
        """
        Initialize the DataplexConnector.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.client = datacatalog_v1.DataCatalogClient()
        self.schema_store = {}

    def fetch_all_entities(self) -> list[datacatalog_v1.Entry]:
        logger.app(f"Searching for all BigQuery table entities in project: {self.project_id}")
        scope = datacatalog_v1.SearchCatalogRequest.Scope()
        scope.include_project_ids.append(self.project_id)

        query = "system=bigquery type=table"
        results = self.client.search_catalog(scope=scope, query=query)

        datasets_tables = defaultdict(list)
        for result in results:
            parts = result.linked_resource.split("/")
            datasets_tables[parts[-3]].append(parts[-1])

        logger.app(f"Found tables across {len(datasets_tables)} datasets.")
        return dict(datasets_tables)

    def fetch_schema(self, linked_resource: str, location: str) -> Optional[Schema]:
        logger.debug(f"Fetching schema for resource: {linked_resource} in location: {location}")
        try:
            request = datacatalog_v1.LookupEntryRequest(
                linked_resource=linked_resource,
                location=location
            )
            entry = self.client.lookup_entry(request=request)

            def format_column(column):
                return {
                    "column_name": column.column,
                    "data_type": column.type_,
                    "description": column.description
                }

            schema = multi_thread(list(entry.schema.columns), format_column)
            return schema
        except NotFound:
            logger.warning(f"Entry not found for resource: {linked_resource}")
            return None
        except GoogleAPICallError as e:
            logger.error(f"Error fetching schema: {e}")
            return None