import logging
from typing import Any, Dict

from rag_agents.data_analysis.graph.state import GraphState
from rag_agents.data_analysis.chains.sql_generation import get_generation_chain
from config import Config, GCPConfig

logger = logging.getLogger(__name__)

def generate_sql(graph_state: GraphState) -> GraphState:
    question = graph_state.question
    schemas = graph_state.schemas

    logger.info(f"Generating SQL for question: {question}")
    chain = get_generation_chain()
    generation = chain.invoke({"question": question, "schemas": schemas})
    logger.info("Generation completed.")
    graph_state.generation = generation

    return graph_state