import logging
from typing import Any, Dict

from agents.insight_pilot.graph.state import GraphState
from agents.insight_pilot.chains.generation import generation_chain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate(graph_state: GraphState) -> Dict[str, Any]:
    question = graph_state['question']
    documents = graph_state['documents']

    logger.info(f"Generating response for question: {question}")
    generation = generation_chain.invoke({"question": question, "context": documents})
    logger.info("Generation completed.")

    return({
        "question": question,
        "generation": generation,
        "documents": documents
    })