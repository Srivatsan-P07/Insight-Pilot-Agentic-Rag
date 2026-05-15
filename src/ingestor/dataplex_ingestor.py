from ingestor.dataplex_connector import DataplexConnector
from ingestor.bigquery_connector import BigQueryConnector
from vectordb.pgvector import PGVectorDB
from config import Config, GCPConfig

import asyncio

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class DataplexIngestor:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.embedder = GCPConfig.embedding_model
        self.connector = DataplexConnector(project_id=project_id)
        self.bq_conn = BigQueryConnector(project_id=project_id)
    
    async def ingest(self):
        # Get Entities and build table IDs
        entities = self.connector.fetch_all_entities()
        table_ids = [
            f"{self.project_id}.{dataset_}.{table_name}"
            for dataset_, tables_ in entities.items()
            for table_name in tables_
        ]

        # Fetch modified times and schemas
        table_id_modified = {
            table: self.bq_conn.get_table(table).modified.astimezone().isoformat()
            for table in table_ids
        }

        table_schema = {}
        for table_full_id in table_ids:
            project_id, dataset_id, table_name = table_full_id.split(".")
            linked_resource = f"//bigquery.googleapis.com/projects/{project_id}/datasets/{dataset_id}/tables/{table_name}"
            schema = self.connector.fetch_schema(linked_resource, location="us-central1")
            
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
                'embedding': self.embedder.embed_query(str(schema[0])),
                'metadata': {"modified_time": schema[1]}
            }
            for table, schema in table_schema.items()
        ]

        await pgvector_db.store_embeddings(docs_without_content)
        await pgvector_db.close()