import logging
from typing import Any, Dict

from rag_agents.data_analysis.graph.state import GraphState
from rag_agents.data_analysis.chains.sql_generation import generation_chain
from config import Config, GCPConfig, AppLogger

logger = AppLogger.setup()

def generate_sql(graph_state: GraphState) -> GraphState:
    question = graph_state.question
    schemas = graph_state.schemas

    logger.app(f"Generating SQL for question: {question}")
    generation = generation_chain.invoke({"question": question, "schemas": schemas})
    logger.app("Generation completed.")
    graph_state.generation = generation

    return graph_state