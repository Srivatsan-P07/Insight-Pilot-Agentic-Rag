import tracemalloc
import asyncio
from agents.insight_pilot.langgraph_rag.nodes.retrieve import retrieve
from agents.insight_pilot.langgraph_rag.graph.state import GraphState
from vectordb.pgvector import PGVectorDB
from config import Config
from agents.insight_pilot.langgraph_rag.nodes.grade_documents import gradedocuments
from agents.insight_pilot.langgraph_rag.nodes.generate import generate
from ingestor.confluence_connector  import ConfluenceConnector
from agents.insight_pilot.langgraph_rag.graph.graph import app

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_retrieve():
    question = "What is Modamart?"

    graph_state = GraphState(
        question=question,
        generation=None,
        documents=[],
        source='confluence'
    )
    print(await app.ainvoke(input=graph_state))

asyncio.run(test_retrieve())