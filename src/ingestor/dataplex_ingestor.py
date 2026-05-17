from ingestor.dataplex_connector import DataplexConnector
from ingestor.bigquery_connector import BigQueryConnector
from vectordb.pgvector import PGVectorDB
from config import Config, GCPConfig, AppLogger, embedding_model
from utils import multi_thread


import asyncio

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class DataplexIngestor:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.embedder = embedding_model
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

        def process_table_schema(table_full_id):
            project_id, dataset_id, table_name = table_full_id.split(".")
            linked_resource = f"//bigquery.googleapis.com/projects/{project_id}/datasets/{dataset_id}/tables/{table_name}"
            schema = self.connector.fetch_schema(linked_resource, location="us-central1")

            modified_time = {"modified_time": table_id_modified[table_full_id]}
            return table_full_id, [schema, modified_time]

        table_schema_results = multi_thread(table_ids, process_table_schema)
        table_schema = dict(table_schema_results)

        # Store embeddings
        pgvector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "dataplex")
        await pgvector_db.connect()

        def prepare_doc(item):
            table, schema = item
            return {
                'source_type': "dataplex",
                'external_id': table,
                'embedding': self.embedder.embed_query(str(schema[0])),
                'metadata': {"modified_time": schema[1]}
            }

        docs_without_content = multi_thread(list(table_schema.items()), prepare_doc)

        await pgvector_db.store_embeddings(docs_without_content)
        await pgvector_db.close()