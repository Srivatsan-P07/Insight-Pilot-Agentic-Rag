from typing import Any, Dict
from rag_agents.data_analysis.graph.state import GraphState
from vectordb.pgvector import PGVectorDB
from config import Config, GCPConfig, AppLogger
from ingestor.dataplex_connector import DataplexConnector
from utils import multi_thread


logger = AppLogger.setup()


async def retrieve(graph_state: GraphState) -> Dict[str, Any]:
    """
    Retrieves relevant table schemas from the vector database based on the user question.

    Args:
        graph_state: The current state of the graph containing the question and source.

    Returns:
        graph_state: Updated state with the list of retrieved schemas.
    """
    question = graph_state.question
    source = graph_state.source

    if source == "dataplex":

        logger.app(f"Retrieving schemas for question: '{question}' from source: {source}")

        vector_db = PGVectorDB(connection_string=Config.PGVECTOR_CONNECTION_STRING, source_type=source)
        dataplex_connector = DataplexConnector(project_id=GCPConfig.GCP_PROJECT_ID)

        retrieved_schemas = []
        try:
            await vector_db.connect()
            similar_tables = await vector_db.query_similar(text=question, top_k=5)

            def fetch_schema_task(entry):
                full_table_id = entry.get("external_id")
                project_id, dataset_id, table_name = full_table_id.split(".")
                linked_resource = f"//bigquery.googleapis.com/projects/{project_id}/datasets/{dataset_id}/tables/{table_name}"
                schema_details = dataplex_connector.fetch_schema(linked_resource=linked_resource, location="us-central1")
                return {
                    "table_name": full_table_id,
                    "schema": schema_details
                }

            results = multi_thread(similar_tables, fetch_schema_task)
            graph_state.schemas = [r for r in results if r is not None]

        finally:
            await vector_db.close()

    return graph_state