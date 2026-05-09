import logging
from typing import Any, Dict

from rag_agents.confluence_assistant.graph.state import GraphState
from rag_agents.confluence_assistant.chains.generation import generation_chain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate(graph_state: GraphState) -> GraphState:
    question = graph_state.question
    documents = graph_state.documents
    chat_history = graph_state.chat_history

    logger.info(f"Generating response for question: {question}")
    generation = generation_chain.invoke({"chat_history": chat_history, "question": question, "context": documents})
    logger.info("Generation completed.")
    graph_state.generation = generation

    return graph_state