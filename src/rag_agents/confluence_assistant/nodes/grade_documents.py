import logging
from typing import Any, Dict
from rag_agents.confluence_assistant.chains.retrieval_grader import get_retrieval_grader
from rag_agents.confluence_assistant.graph.state import GraphState
from config import Config, GCPConfig

logger = logging.getLogger(__name__)

async def gradedocuments(graph_state: GraphState) -> Dict[str, Any]:
    question = graph_state.question
    documents = graph_state.documents

    logger.info(f"Grading {len(documents)} documents for question: {question}")
    if not documents:
        return graph_state

    # Documents are strings containing "Document {idx} - Title: ... Content: ..."
    formatted_docs = "\n\n".join(documents)

    chain = get_retrieval_grader()
    batch_score = await chain.ainvoke({"question": question, "documents": formatted_docs})

    relevant_indices = {res.document_id for res in batch_score.results if res.is_relevant}
    filtered_docs = [doc for i, doc in enumerate(documents) if i in relevant_indices]

    logger.info(f"Retained {len(filtered_docs)} relevant documents out of {len(documents)}.")

    graph_state.documents = filtered_docs
    return graph_state