import logging
from typing import Any, Dict
from agents.insight_pilot.graph.state import GraphState
from vectordb.pgvector import PGVectorDB
from config import Config
from ingestor.confluence_connector import ConfluenceConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def retrieve(graph_state: GraphState) -> Dict[str, Any]:
    """
    Retrieves relevant documents from the vector database based on the current graph state.

    Args:
        graph_state: The current state of the graph, which includes the question and any relevant documents or nodes.

    Returns:
        graph_state: The updated state of the graph with the retrieved documents.
    """
    question = graph_state["question"]
    source = graph_state.get("source", "")
    documents = graph_state.get("documents", [])

    if source == 'confluence':
        logger.info(f"Retrieving documents for: {question} from {source}")
        
        # Initialize DB and Connector
        vector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "confluence")
        connector = ConfluenceConnector(
            Config.confluence_url,
            Config.confluence_username,
            Config.confluence_api_key
        )

        try:
            await vector_db.connect()
            search_results = await vector_db.query_similar(question, 1)

            for result in search_results:
                page_id = result.get('external_id')
                page_title = result.get('metadata', {}).get('title', 'Untitled')

                # Fetch full content from Confluence
                page_data = connector.fetch_page_by_id(page_id)
                content = page_data.get('content', '')
                
                documents.append(f"Title: {page_title}\nContent: {content}")
            
            graph_state["documents"] = documents
        finally:
            await vector_db.close()

    return graph_state