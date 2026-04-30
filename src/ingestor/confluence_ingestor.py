from config import Config
from ingestor.confluence_connector import ConfluenceConnector
from vectordb.pgvector import PGVectorDB
from ollama_rag.ollama_config import OllamaEmbedder

import asyncio

class ConfluenceIngestorPipeline:
    def __init__(self):
        self.config = Config()
        self.pgvector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "confluence")
        self.embedder = OllamaEmbedder()
        self.ingestor = None
    
    async def initialize(self):
        await self.pgvector_db.connect()
        self.ingestor = ConfluenceConnector(
            self.config.confluence_url,
            self.config.confluence_username,
            self.config.confluence_api_key
        )
    
    async def run(self):
        # Run Ingestors
        result = self.ingestor.sync(
            space_key=self.config.confluence_space_key,
            last_sync_time="2025-04-25T10:00:00Z"
        )
        
        # Embed Content
        docs_without_content = [
            {
                'source_type': "confluence",
                'external_id': doc['external_id'],
                'embedding': self.embedder.embed_text(doc['content']),
                'metadata': doc['metadata']
            }
            for doc in result["updated_pages"]
        ]
        
        # Store in PGVector
        await self.pgvector_db.store_embeddings(docs_without_content)
    
    async def close(self):
        await self.pgvector_db.close()