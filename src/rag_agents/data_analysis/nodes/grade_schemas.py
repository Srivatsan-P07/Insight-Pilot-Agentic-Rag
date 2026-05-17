import logging
from typing import Any, Dict
from rag_agents.data_analysis.chains.retrieval_grader import retrieval_grader
from rag_agents.data_analysis.graph.state import GraphState
from config import Config, GCPConfig, AppLogger
from utils import multi_thread


logger = AppLogger.setup()

def gradeschemas(graph_state: GraphState) -> Dict[str, Any]:
    """
    Determines whether the retrieved schemas are required to the question
    If a schema is not relevant, it is filtered out.

    Args:
        graph_state (GraphState): The current graph state

    Returns:
        graph_state (GraphState): Updated state with filtered relevant schemas
    """
    question = graph_state.question
    schemas = graph_state.schemas

    logger.app(f"Grading {len(schemas)} schemas for question: {question}")

    def grade_schema(schema):
        score = retrieval_grader.invoke({"question": question, "schema": schema})
        if score.binary_score.lower() == "yes":
            logger.app("--- GRADE: SCHEMA RELEVANT ---")
            return schema
        else:
            logger.app("--- GRADE: SCHEMA NOT RELEVANT ---")
            return None

    results = multi_thread(schemas,grade_schema)
    filtered_schemas = [s for s in results if s is not None]
    
    graph_state.schemas = filtered_schemas
    return graph_state