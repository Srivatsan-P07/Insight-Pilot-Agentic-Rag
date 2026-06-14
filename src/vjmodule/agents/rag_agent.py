from __future__ import annotations

from typing import Generator

from config import Config
from connectors.qdrant import QdrantConnector


def stream_confluence(question: str) -> Generator[str, None, None]:
    """Yield a streaming Confluence / vector-DB answer for *question*."""
    qdrant = QdrantConnector()
    try:
        if not qdrant.get_collection(Config.qdrant_collection_name):
            yield f"⚠️ Qdrant collection `{Config.qdrant_collection_name}` not found."
            return
    except Exception as exc:
        yield f"⚠️ Could not connect to Qdrant: {exc}"
        return

    try:
        relevant_docs = qdrant.similarity_search(
            Config.qdrant_collection_name, question, top_k=4
        )
        context = "\n\n".join(
            f"**{doc['payload']['title']}**\n{doc['payload']['content']}"
            for doc in relevant_docs
        )
        prompt = (
            f"Based on the following documentation:\n\n{context}\n\n"
            f"Answer this question: {question}\n\n"
            "If the documentation does not contain enough information, explain why and "
            "suggest where to find the answer. Use markdown formatting."
        )
        for chunk in Config.llm.stream(prompt):
            if chunk.content:
                yield chunk.content
    except Exception as exc:
        yield f"\n\n\u274c **Error:** {exc}"


def query_confluence(question: str) -> str:
  """Retrieves relevant docs from VectorDB and answers the question."""

  qdrant = QdrantConnector()
  if not qdrant.get_collection(Config.qdrant_collection_name):
    raise Exception(f"Collection '{Config.qdrant_collection_name}' does not exist in Qdrant.")

  # Perform similarity search
  relevant_docs = qdrant.similarity_search(Config.qdrant_collection_name, question, top_k=4)
  context = "\n\n".join(
    "title: " + doc['payload']['title'] + "\ncontent: " + doc['payload']['content'] for doc in relevant_docs
  )

  # Pass context to LLM
  prompt = (
    f"Based on the following documentation:\n\n{context}\n\n"
    f"Answer the question: {question}\n\n"
    f"If the documentation does not contain enough information, say why and suggest how to find the answer."
  )
  return Config.llm.invoke(prompt).content.strip()