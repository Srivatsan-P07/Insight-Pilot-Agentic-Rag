from config import Config
from ingestor.confluence_ingestor import ConfluenceIngestor
from vectordb.pgvector import PGVectorDB
from ollama_rag.ollama_config import OllamaEmbedder

import asyncio

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    config = Config()
    pgvector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "confluence")
    embedder = OllamaEmbedder()  # Create once, reuse
    
    await pgvector_db.connect()
    
    # Initialize Ingestors
    ingestor = ConfluenceIngestor(
        config.confluence_url, 
        config.confluence_username, 
        config.confluence_api_key
    )

    # Run Ingestors
    result = ingestor.sync(
        space_key=config.confluence_space_key,
        last_sync_time="2025-04-25T10:00:00Z"
    )

    # Embed Content
    docs_without_content = [
        {
            'source_type': "confluence",
            'external_id': doc['external_id'],
            'embedding': embedder.embed_text(doc['content']),
            'metadata': doc['metadata']
        }
        for doc in result["updated_pages"]
    ]

    # Store in PGVector
    await pgvector_db.store_embeddings(docs_without_content)
    await pgvector_db.close()

if __name__ == "__main__":
    asyncio.run(main())