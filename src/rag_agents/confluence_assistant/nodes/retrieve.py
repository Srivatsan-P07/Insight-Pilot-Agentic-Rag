from config import Config, GCPConfig
from typing import Any, Dict
from rag_agents.confluence_assistant.graph.state import GraphState
from vectordb.pgvector import PGVectorDB
from ingestor.confluence_connector import ConfluenceConnector
import logging
from tracing import trace_node

logger = logging.getLogger(__name__)

@trace_node("confluence_retrieve")
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
        logger.info(f"Retrieving documents for: {question} from {source}")
        
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

            async def fetch_content(result, idx):
                page_id = result.get('external_id')
                page_title = result.get('metadata', {}).get('title', 'Untitled')
                # Fetch full content from Confluence asynchronously
                page_data = await connector.fetch_page_by_id(page_id)
                content = page_data.get('content', '') if page_data else ''
                return f"Document {idx} - Title: {page_title}\nContent: {content}"

            import asyncio
            fetched_docs = await asyncio.gather(*(fetch_content(res, i) for i, res in enumerate(search_results)))
            documents.extend(fetched_docs)
            
            graph_state.documents = documents
        finally:
            await vector_db.close()
            await connector.close()

    return graph_state