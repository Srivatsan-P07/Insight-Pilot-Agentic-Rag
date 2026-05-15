from config import Config, GCPConfig
from ingestor.confluence_connector import ConfluenceConnector
from vectordb.pgvector import PGVectorDB

import asyncio
import logging

logger = logging.getLogger(__name__)

class ConfluenceIngestorPipeline:
    def __init__(self):
        self.config = Config()
        self.pgvector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "confluence")
        self.embedder = GCPConfig.embedding_model
        self.ingestor = None
    
    async def initialize(self):
        logger.info("Initializing Confluence Ingestor Pipeline...")
        await self.pgvector_db.connect()
        self.ingestor = ConfluenceConnector(
            self.config.CONFLUENCE_URL,
            self.config.CONFLUENCE_USERNAME,
            self.config.CONFLUENCE_API_KEY
        )
    
    async def run(self):
        logger.info(f"Starting Confluence sync for space: {self.config.CONFLUENCE_SPACE_KEY}")
        # Run Ingestors
        result = self.ingestor.sync(
            space_key=self.config.CONFLUENCE_SPACE_KEY,
            last_sync_time="2025-04-25T10:00:00Z"
        )
        
        if not result["updated_pages"]:
            logger.info("No new or updated pages found to process.")
            return

        logger.info(f"Embedding {len(result['updated_pages'])} pages...")
        # Embed Content
        docs_to_store = [
            {
                'source_type': "confluence",
                'external_id': doc['external_id'],
                'embedding': self.embedder.embed_query(doc['content']),
                'metadata': doc['metadata']
            }
            for doc in result["updated_pages"]
        ]
        
        logger.info(f"Storing embeddings in PGVector...")
        await self.pgvector_db.store_embeddings(docs_to_store)
        logger.info("Confluence ingestion pipeline completed successfully.")
    
    async def close(self):
        await self.pgvector_db.close()
        logger.info("Confluence Ingestor Pipeline closed.")