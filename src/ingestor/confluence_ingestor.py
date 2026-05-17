from config import Config, GCPConfig, AppLogger, embedding_model
from ingestor.confluence_connector import ConfluenceConnector
from vectordb.pgvector import PGVectorDB
from utils import multi_thread

import asyncio
logger = AppLogger.setup()
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class ConfluenceIngestorPipeline:
    def __init__(self):
        self.config = Config()
        self.pgvector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "confluence")
        self.embedder = embedding_model
        self.ingestor = None
    
    async def initialize(self):
        logger.app("Initializing Confluence Ingestor Pipeline...")
        await self.pgvector_db.connect()
        self.ingestor = ConfluenceConnector(
            self.config.CONFLUENCE_URL,
            self.config.CONFLUENCE_USERNAME,
            self.config.CONFLUENCE_API_KEY
        )
    
    async def run(self):
        logger.app(f"Starting Confluence sync for space: {self.config.CONFLUENCE_SPACE_KEY}")
        # Run Ingestors
        result = self.ingestor.sync(
            space_key=self.config.CONFLUENCE_SPACE_KEY,
            last_sync_time="2025-04-25T10:00:00Z"
        )
        
        if not result["updated_pages"]:
            logger.app("No new or updated pages found to process.")
            return

        logger.app(f"Embedding {len(result['updated_pages'])} pages...")

        def prepare_doc(doc):
            try:
                content = (doc.get("content") or "").strip()

                if not content:
                    print(f"Skipping empty document: {doc.get('external_id')}")
                    return None
                
                return {
                    'source_type': "confluence",
                    'external_id': doc['external_id'],
                    'embedding': self.embedder.embed_query(doc['content']),
                    'metadata': doc['metadata']
                }

            except Exception as e:
                logger.exception(f"Failed embedding doc {doc['external_id']}")
                return None

        # Embed Content
        docs_to_store = multi_thread(result["updated_pages"], prepare_doc)
        
        logger.app(f"Storing embeddings in PGVector...")
        await self.pgvector_db.store_embeddings(docs_to_store)
        logger.app("Confluence ingestion pipeline completed successfully.")
    
    async def close(self):
        await self.pgvector_db.close()
        logger.app("Confluence Ingestor Pipeline closed.")