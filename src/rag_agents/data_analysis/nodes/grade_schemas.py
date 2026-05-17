import logging
from typing import Any, Dict
from rag_agents.data_analysis.chains.retrieval_grader import create_retrieval_grader
from rag_agents.data_analysis.graph.state import GraphState
from config import Config, GCPConfig

logger = logging.getLogger(__name__)

async def gradeschemas(graph_state: GraphState) -> Dict[str, Any]:
    question = graph_state.question
    schemas = graph_state.schemas

    logger.info(f"Grading {len(schemas)} schemas for question: {question}")
    if not schemas:
        return graph_state

    formatted_schemas = "\n\n".join([f"Table: {s['table_name']}\nSchema: {s['schema']}" for s in schemas])
    
    chain = create_retrieval_grader()
    grade_response = await chain.ainvoke({"question": question, "schemas": formatted_schemas})
    
    if grade_response.binary_score == "yes":
        filtered_schemas = schemas
    else:
        filtered_schemas = []
    
    logger.info(f"Retained {len(filtered_schemas)} relevant schemas out of {len(schemas)}.")
    
    graph_state.schemas = filtered_schemas
    return graph_state