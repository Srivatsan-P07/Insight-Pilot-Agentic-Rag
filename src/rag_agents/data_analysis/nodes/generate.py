import logging
from typing import Any, Dict

from rag_agents.data_analysis.graph.state import GraphState
from rag_agents.data_analysis.chains.generation import generation_chain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate(graph_state: GraphState) -> GraphState:
    question = graph_state.question
    schemas = graph_state.schemas
    chat_history = graph_state.chat_history

    logger.info(f"Generating response for question: {question}")
    generation = generation_chain.invoke({"chat_history": chat_history, "question": question, "context": schemas})
    logger.info("Generation completed.")
    graph_state.generation = generation

    return graph_state