import logging
from typing import Optional
from google.cloud import dataplex_v1
from google.cloud.dataplex_v1.types import Schema
from google.api_core.exceptions import NotFound, GoogleAPICallError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataplexIngestor:
    """
    Handles ingestion of schemas from Google Cloud Dataplex.
    Supports fetching updated schemas and deleting schemas for removed tables.
    """

    def __init__(self, project_id: str, location: str, lake_id: str, zone_id: str):
        """
        Initialize the DataplexIngestor.

        Args:
            project_id: GCP project ID
            location: GCP region (e.g., 'us-central1')
            lake_id: Dataplex lake ID
            zone_id: Dataplex zone ID
        """
        self.project_id = project_id
        self.location = location
        self.lake_id = lake_id
        self.zone_id = zone_id
        self.client = dataplex_v1.MetadataServiceClient()
        self.schema_store: dict[str, Schema] = {}

    def _build_entity_name(self, entity_id: str) -> str:
        return (
            f"projects/{self.project_id}/locations/{self.location}"
            f"/lakes/{self.lake_id}/zones/{self.zone_id}/entities/{entity_id}"
        )

    def _build_zone_name(self) -> str:
        return (
            f"projects/{self.project_id}/locations/{self.location}"
            f"/lakes/{self.lake_id}/zones/{self.zone_id}"
        )

    def fetch_all_entities(self) -> list[dataplex_v1.Entity]:
        """
        Fetch all entities (tables) in the specified zone.

        Returns:
            List of Dataplex Entity objects.
        """
        try:
            request = dataplex_v1.ListEntitiesRequest(parent=self._build_zone_name())
            entities = list(self.client.list_entities(request=request))
            logger.info(f"Fetched {len(entities)} entities from Dataplex.")
            return entities
        except GoogleAPICallError as e:
            logger.error(f"Failed to fetch entities: {e}")
            return []

    def fetch_schema(self, entity_id: str) -> Optional[Schema]:
        """
        Fetch schema for a specific entity/table.

        Args:
            entity_id: The entity ID to fetch schema for.

        Returns:
            Schema object or None if not found.
        """
        try:
            entity_name = self._build_entity_name(entity_id)
            request = dataplex_v1.GetEntityRequest(name=entity_name)
            entity = self.client.get_entity(request=request)
            schema = entity.schema_
            logger.info(f"Fetched schema for entity: {entity_id}")
            return schema
        except NotFound:
            logger.warning(f"Entity not found: {entity_id}")
            return None
        except GoogleAPICallError as e:
            logger.error(f"Error fetching schema for entity {entity_id}: {e}")
            return None

    def fetch_updated_schemas(self) -> dict[str, Schema]:
        """
        Fetch schemas for all entities and update the internal schema store.
        Detects new and updated schemas.

        Returns:
            Dictionary of entity_id -> Schema for new/updated schemas.
        """
        updated_schemas = {}
        try:
            entities = self.fetch_all_entities()
            if not entities:
                logger.info("No entities found.")
                return updated_schemas

            for entity in entities:
                entity_id = entity.name.split("/")[-1]
                schema = entity.schema_

                if schema is None:
                    logger.warning(f"No schema found for entity: {entity_id}, skipping.")
                    continue

                existing_schema = self.schema_store.get(entity_id)

                if existing_schema is None:
                    logger.info(f"New schema detected for entity: {entity_id}")
                    self.schema_store[entity_id] = schema
                    updated_schemas[entity_id] = schema
                elif existing_schema != schema:
                    logger.info(f"Updated schema detected for entity: {entity_id}")
                    self.schema_store[entity_id] = schema
                    updated_schemas[entity_id] = schema

        except Exception as e:
            logger.error(f"Unexpected error during schema fetch: {e}")

        logger.info(f"Total new/updated schemas: {len(updated_schemas)}")
        return updated_schemas

    def delete_removed_schemas(self) -> list[str]:
        """
        Detect and remove schemas for tables/entities that no longer exist in Dataplex.

        Returns:
            List of entity IDs whose schemas were deleted.
        """
        deleted_entity_ids = []
        try:
            entities = self.fetch_all_entities()
            active_entity_ids = {entity.name.split("/")[-1] for entity in entities}
            stored_entity_ids = set(self.schema_store.keys())

            removed_entities = stored_entity_ids - active_entity_ids

            for entity_id in removed_entities:
                logger.info(f"Entity {entity_id} no longer exists. Deleting schema.")
                del self.schema_store[entity_id]
                deleted_entity_ids.append(entity_id)

        except Exception as e:
            logger.error(f"Unexpected error during schema deletion: {e}")

        logger.info(f"Total schemas deleted: {len(deleted_entity_ids)}")
        return deleted_entity_ids

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

    def get_schema(self, entity_id: str) -> Optional[Schema]:
        """
        Retrieve a cached schema for a given entity.

        Args:
            entity_id: The entity ID.

        Returns:
            Cached Schema or None.
        """
        schema = self.schema_store.get(entity_id)
        if not schema:
            logger.warning(f"No cached schema found for entity: {entity_id}")
        return schema

    def get_all_schemas(self) -> dict[str, Schema]:
        """
        Return all cached schemas.

        Returns:
            Dictionary of entity_id -> Schema.
        """
        return self.schema_store.copy()