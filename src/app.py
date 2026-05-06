import tracemalloc
import asyncio
from langgraph_rag.nodes.retrieve import retrieve
from langgraph_rag.graph.state import GraphState
from vectordb.pgvector import PGVectorDB
from config import Config
from langgraph_rag.nodes.grade_documents import gradedocuments
from langgraph_rag.nodes.generate import generate
from ingestor.confluence_connector  import ConfluenceConnector
from langgraph_rag.graph.graph import app
import chainlit as cl

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@cl.step(type="tool")
async def tool(question: str) -> str:
    graph_state = GraphState(
        question=question,
        generation=None,
        documents=[],
        source='confluence'
    )
    graph_state_dict = await app.ainvoke(input=graph_state)
    return (graph_state_dict.get("generation") or "No answer generated.")

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user messages and send responses."""
    text = await tool(message.content)
    await cl.Message(content=text).send()