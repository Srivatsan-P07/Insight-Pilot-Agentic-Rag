import logging
from typing import Optional
from google.cloud import datacatalog_v1
from google.cloud.datacatalog_v1.types import Schema
from google.api_core.exceptions import NotFound, GoogleAPICallError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        self.schema_store: dict[str, Schema] = {}

    def fetch_all_entities(self) -> list[datacatalog_v1.Entry]:
        """
        Fetch all entries from Data Catalog.

        Returns:
            List of Data Catalog Entry objects.
        """
        try:
            request = datacatalog_v1.SearchCatalogRequest(
                scope=datacatalog_v1.SearchCatalogRequest.Scope(
                    include_project_ids=[self.project_id]
                )
            )
            entries = list(self.client.search_catalog(request=request))
            logger.info(f"Fetched {len(entries)} entries from Data Catalog.")
            return entries
        except GoogleAPICallError as e:
            logger.error(f"Failed to fetch entries: {e}")
            return []

    def fetch_schema(self, linked_resource: str, location: str) -> Optional[Schema]:
        try:
            request = datacatalog_v1.LookupEntryRequest(
                linked_resource=linked_resource,
                location=location
            )
            entry = self.client.lookup_entry(request=request)
            schema = [
            {
                "column_name": column.column,
                "data_type": column.type_,
                "description": column.description
            }
            for column in entry.schema.columns
            ]
            logger.info(f"Fetched schema for resource: {linked_resource}")
            return schema
        except NotFound:
            logger.warning(f"Entry not found for resource: {linked_resource}")
            return None
        except GoogleAPICallError as e:
            logger.error(f"Error fetching schema: {e}")
            return None

    def fetch_updated_schemas(self) -> dict[str, Schema]:
        """
        Fetch schemas for all entries and update the internal schema store.
        Detects new and updated schemas.

        Returns:
            Dictionary of entry_id -> Schema for new/updated schemas.
        """
        updated_schemas = {}
        try:
            entries = self.fetch_all_entities()
            if not entries:
                logger.info("No entries found.")
                return updated_schemas

            for entry in entries:
                entry_id = entry.name
                schema = entry.schema_

                if schema is None:
                    logger.warning(f"No schema found for entry: {entry_id}, skipping.")
                    continue

                existing_schema = self.schema_store.get(entry_id)

                if existing_schema is None:
                    logger.info(f"New schema detected for entry: {entry_id}")
                    self.schema_store[entry_id] = schema
                    updated_schemas[entry_id] = schema
                elif existing_schema != schema:
                    logger.info(f"Updated schema detected for entry: {entry_id}")
                    self.schema_store[entry_id] = schema
                    updated_schemas[entry_id] = schema

        except Exception as e:
            logger.error(f"Unexpected error during schema fetch: {e}")

        logger.info(f"Total new/updated schemas: {len(updated_schemas)}")
        return updated_schemas

    def delete_removed_schemas(self) -> list[str]:
        """
        Detect and remove schemas for entries that no longer exist in Data Catalog.

        Returns:
            List of entry IDs whose schemas were deleted.
        """
        deleted_entry_ids = []
        try:
            entries = self.fetch_all_entities()
            active_entry_ids = {entry.name for entry in entries}
            stored_entry_ids = set(self.schema_store.keys())

            removed_entries = stored_entry_ids - active_entry_ids

            for entry_id in removed_entries:
                logger.info(f"Entry {entry_id} no longer exists. Deleting schema.")
                del self.schema_store[entry_id]
                deleted_entry_ids.append(entry_id)

        except Exception as e:
            logger.error(f"Unexpected error during schema deletion: {e}")

        logger.info(f"Total schemas deleted: {len(deleted_entry_ids)}")
        return deleted_entry_ids

    def sync_schemas(self) -> dict:
        """
        Full sync: fetch updated schemas and delete removed schemas.

        Returns:
            Dictionary with 'updated' and 'deleted' keys.
        """
        logger.info("Starting full schema sync...")
        updated = self.fetch_updated_schemas()
        deleted = self.delete_removed_schemas()
        logger.info(f"Sync complete. Updated: {len(updated)}, Deleted: {len(deleted)}")
        return {"updated": updated, "deleted": deleted}

    def get_schema(self, entry_id: str) -> Optional[Schema]:
        """
        Retrieve a cached schema for a given entry.

        Args:
            entry_id: The entry ID.

        Returns:
            Cached Schema or None.
        """
        schema = self.schema_store.get(entry_id)
        if not schema:
            logger.warning(f"No cached schema found for entry: {entry_id}")
        return schema

    def get_all_schemas(self) -> dict[str, Schema]:
        """
        Return all cached schemas.

        Returns:
            Dictionary of entry_id -> Schema.
        """
        return self.schema_store.copy()
