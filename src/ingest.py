from ingestor.dataplex_ingestor import DataplexIngestor
from ingestor.confluence_ingestor import ConfluenceIngestorPipeline
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    # ingest confluence data
    """pipeline = ConfluenceIngestorPipeline()
    await pipeline.initialize()
    await pipeline.run()
    await pipeline.close()"""

    # ingest dataplex data
    PROJECT_ID = "insight-pilot-trios"
    ingestor = DataplexIngestor(PROJECT_ID)
    await ingestor.ingest()

if __name__ == "__main__":
    asyncio.run(main())