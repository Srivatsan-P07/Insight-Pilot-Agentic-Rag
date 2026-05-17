from config import Config, GCPConfig, AppLogger
from typing import Any, Dict
from rag_agents.confluence_assistant.graph.state import GraphState
from vectordb.pgvector import PGVectorDB
from config import Config
from ingestor.confluence_connector import ConfluenceConnector
from utils import multi_thread


logger = AppLogger.setup()

async def retrieve(graph_state: GraphState) -> Dict[str, Any]:
    """
    Retrieves relevant documents from the vector database based on the current graph state.

    Args:
        graph_state: The current state of the graph, which includes the question and any relevant documents or nodes.

    Returns:
        graph_state: The updated state of the graph with the retrieved documents.
    """
    question = graph_state.question
    source = graph_state.source
    documents = graph_state.documents

    if source == 'confluence':
        logger.app(f"Retrieving documents for: {question} from {source}")
        
        # Initialize DB and Connector
        vector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "confluence")
        connector = ConfluenceConnector(
            Config.CONFLUENCE_URL,
            Config.CONFLUENCE_USERNAME,
            Config.CONFLUENCE_API_KEY
        )

        try:
            await vector_db.connect()
            search_results = await vector_db.query_similar(question, 5)

            def fetch_content(result):
                page_id = result.get('external_id')
                page_title = result.get('metadata', {}).get('title', 'Untitled')
                # Fetch full content from Confluence
                page_data = connector.fetch_page_by_id(page_id)
                content = page_data.get('content', '')
                return f"Title: {page_title}\nContent: {content}"

            fetched_docs = multi_thread(search_results,fetch_content)
            documents.extend(fetched_docs)
            
            graph_state.documents = documents
        finally:
            await vector_db.close()

    return graph_state