import tracemalloc
import asyncio
from rag_agents.insight_pilot.nodes.retrieve import retrieve
from rag_agents.insight_pilot.graph.state import GraphState
from vectordb.pgvector import PGVectorDB
from config import Config
from rag_agents.insight_pilot.nodes.grade_documents import gradedocuments
from rag_agents.insight_pilot.nodes.generate import generate
from ingestor.confluence_connector  import ConfluenceConnector
from rag_agents.insight_pilot.graph.graph import app

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