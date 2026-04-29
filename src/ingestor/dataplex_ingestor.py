from ingestor.dataplex_connector import DataplexConnector
from ingestor.bigquery_connector import BigQueryConnector
from vectordb.pgvector import PGVectorDB
from ollama_rag.ollama_config import OllamaEmbedder
from config import Config

import asyncio

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    PROJECT_ID = "insight-pilot-trios"
    
    embedder = OllamaEmbedder()  # Create once, reuse
    connector = DataplexConnector(project_id=PROJECT_ID)
    bq_conn = BigQueryConnector(project_id=PROJECT_ID)

    # Get Entities and build table IDs
    entities = connector.fetch_all_entities()
    table_ids = [
        f"{PROJECT_ID}.{dataset_}.{table_name}"
        for dataset_, tables_ in entities.items()
        for table_name in tables_
    ]

    # Fetch modified times and schemas
    table_id_modified = {
        table: bq_conn.get_table(table).modified.astimezone().isoformat()
        for table in table_ids
    }

    table_schema = {}
    for table_full_id in table_ids:
        project_id, dataset_id, table_name = table_full_id.split(".")
        linked_resource = f"//bigquery.googleapis.com/projects/{project_id}/datasets/{dataset_id}/tables/{table_name}"
        schema = connector.fetch_schema(linked_resource, location="us-central1")
        
        modified_time = {"modified_time": table_id_modified[table_full_id]}
        commulative_metadata = [schema, modified_time]
        table_schema[table_full_id] = commulative_metadata
    
    # Store embeddings
    pgvector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "dataplex")
    await pgvector_db.connect()

    
    docs_without_content = [
        {
            'source_type': "dataplex",
            'external_id': table,
            'embedding': embedder.embed_text(str(schema[0])),
            'metadata': {"modified_time": schema[1]}
        }
        for table, schema in table_schema.items()
    ]

    await pgvector_db.store_embeddings(docs_without_content)
    await pgvector_db.close()

if __name__ == "__main__":
    asyncio.run(main())