from config import Config, GCPConfig, AppLogger
from typing import Any, Dict
from rag_agents.confluence_assistant.chains.retrieval_grader import retrieval_grader
from rag_agents.confluence_assistant.graph.state import GraphState
from utils import multi_thread

logger = AppLogger.setup()

def gradedocuments(graph_state: GraphState) -> Dict[str, Any]:
    """
    Determines whether the retrieved documents are relevant to the question
    If a document is not relevant, it is filtered out.

    Args:
        graph_state (GraphState): The current graph state

    Returns:
        graph_state (GraphState): Updated state with filtered relevant documents
    """
    chat_history = graph_state.chat_history
    question = graph_state.question
    documents = graph_state.documents

    logger.app(f"Grading {len(documents)} documents for question: {question}")

    def grade_doc(doc):
        score = retrieval_grader.invoke({"question": question, "document": doc})
        is_relevant = score.binary_score.lower() == "yes"
        if is_relevant:
            logger.app("--- GRADE: DOCUMENT RELEVANT ---")
            return doc
        else:
            logger.app("--- GRADE: DOCUMENT NOT RELEVANT ---")
            return None

    results = multi_thread(documents,grade_doc)
    filtered_docs = [doc for doc in results if doc is not None]

    graph_state.documents = filtered_docs
    return graph_state