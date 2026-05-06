import logging
from typing import Any, Dict
from agents.insight_pilot.chains.retrieval_grader import retrieval_grader
from agents.insight_pilot.graph.state import GraphState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def gradedocuments(graph_state: GraphState) -> Dict[str, Any]:
    """
    Determines whether the retrieved documents are relevant to the question
    If a document is not relevant, it is filtered out.

    Args:
        graph_state (GraphState): The current graph state

    Returns:
        graph_state (GraphState): Updated state with filtered relevant documents
    """
    question = graph_state.get("question")
    documents = graph_state.get("documents", [])

    logger.info(f"Grading {len(documents)} documents for question: {question}")
    
    filtered_docs = []
    for doc in documents:
        score = retrieval_grader.invoke({"question": question, "document": doc})
        # Assuming score is a Pydantic model or object with binary_score attribute
        is_relevant = score.binary_score.lower() == "yes"
        
        if is_relevant:
            logger.info("--- GRADE: DOCUMENT RELEVANT ---")
            filtered_docs.append(doc)
        else:
            logger.info("--- GRADE: DOCUMENT NOT RELEVANT ---")

    graph_state["documents"] = filtered_docs
    return graph_state