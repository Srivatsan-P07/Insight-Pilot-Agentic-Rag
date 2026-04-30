from typing import Any, Dict
from langgraph.graph.state import GraphState
from vectordb.pgvector import PGVectorDB

async def retrieve(graph_state: GraphState, vector_db: PGVectorDB) -> Dict[str, Any]:
    """
    Retrieves relevant documents from the vector database based on the current graph state.

    Args:
        graph_state: The current state of the graph, which includes the question and any relevant documents or nodes.
        vector_db: An instance of the PGVectorDB class that allows us to query the vector database.
    """
    # Extract the question from the graph state
    question = graph_state.get("question")

    # Query the vector database for similar documents
    results = await vector_db.query_similar(question)

    return {
        "question": question,
        "results": results
    }