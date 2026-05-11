import logging
from typing import Any, Dict
from rag_agents.data_analysis.chains.retrieval_grader import retrieval_grader
from rag_agents.data_analysis.graph.state import GraphState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def gradeschemas(graph_state: GraphState) -> Dict[str, Any]:
    """
    Determines whether the retrieved schemas are required to the question
    If a schema is not relevant, it is filtered out.

    Args:
        graph_state (GraphState): The current graph state

    Returns:
        graph_state (GraphState): Updated state with filtered relevant schemas
    """
    chat_history = graph_state.chat_history
    question = graph_state.question
    schemas = graph_state.schemas

    logger.info(f"Grading {len(schemas)} schemas for question: {question}")
    
    filtered_schemas = []
    for schema in schemas:
        score = retrieval_grader.invoke({"question": question, "schema": schema})
        # Assuming score is a Pydantic model or object with binary_score attribute
        is_relevant = score.binary_score.lower() == "yes"
        
        if is_relevant:
            logger.info("--- GRADE: SCHEMA RELEVANT ---")
            filtered_schemas.append(schema)
        else:
            logger.info("--- GRADE: SCHEMA NOT RELEVANT ---")

    graph_state.schemas = filtered_schemas
    return graph_state