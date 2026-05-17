from config import Config, GCPConfig
from ingestor.confluence_connector import ConfluenceConnector
from vectordb.pgvector import PGVectorDB
import asyncio
import logging
logger = logging.getLogger(__name__)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class ConfluenceIngestorPipeline:
    def __init__(self):
        self.config = Config()
        self.pgvector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "confluence")
        self.embedder = GCPConfig.get_embedding_model()
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
        result = await self.ingestor.sync(
            space_key=self.config.CONFLUENCE_SPACE_KEY,
            last_sync_time="2025-04-25T10:00:00Z"
        )
        
        if not result["updated_pages"]:
            logger.info("No new or updated pages found to process.")
            return

        logger.info(f"Embedding {len(result['updated_pages'])} pages...")

        async def prepare_doc(doc):
            try:
                content = (doc.get("content") or "").strip()
                if not content:
                    print(f"Skipping empty document: {doc.get('external_id')}")
                    return None
                
                # Use async embedding
                embedding = await self.embedder.aembed_query(content)
                return {
                    'source_type': "confluence",
                    'external_id': doc['external_id'],
                    'embedding': embedding,
                    'metadata': doc['metadata']
                }
            except Exception as e:
                logger.exception(f"Failed embedding doc {doc['external_id']}")
                return None

        # Embed Content asynchronously
        docs_to_store = await asyncio.gather(*(prepare_doc(doc) for doc in result["updated_pages"]))
        docs_to_store = [d for d in docs_to_store if d is not None]
        
        logger.info(f"Storing embeddings in PGVector...")
        if docs_to_store:
            await self.pgvector_db.store_embeddings(docs_to_store)
        logger.info("Confluence ingestion pipeline completed successfully.")
    
    async def close(self):
        await self.pgvector_db.close()
        logger.info("Confluence Ingestor Pipeline closed.")