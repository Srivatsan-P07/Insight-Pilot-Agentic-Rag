import logging
import asyncio
from typing import Any, Dict
from rag_agents.data_analysis.chains.retrieval_grader import create_retrieval_grader
from rag_agents.data_analysis.graph.state import GraphState
from config import Config, GCPConfig
from utils import multi_thread

logger = logging.getLogger(__name__)

async def gradeschemas(graph_state: GraphState) -> Dict[str, Any]:
    question = graph_state.question
    schemas = graph_state.schemas

    logger.info(f"Grading {len(schemas)} schemas for question: {question}")
    if not schemas:
        return graph_state

    chain = create_retrieval_grader()
    filtered_schemas = []

    async def grade_item(schema_item):
        formatted_schema = f"Table: {schema_item['table_name']}\nSchema: {schema_item['schema']}"
        grade_response = await chain.ainvoke({"question": question, "schemas": formatted_schema})
        return schema_item if grade_response.binary_score == "yes" else None

    # Since chain.ainvoke is async, we use asyncio.gather for concurrent execution
    results = await asyncio.gather(*(grade_item(item) for item in schemas))
    
    # Filter out None values
    filtered_schemas = [res for res in results if res is not None]
    
    logger.info(f"Retained {len(filtered_schemas)} relevant schemas out of {len(schemas)}.")
    
    graph_state.schemas = filtered_schemas
    return graph_state