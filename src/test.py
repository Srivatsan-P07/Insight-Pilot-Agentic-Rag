import tracemalloc
import asyncio
from langgraph.nodes.retrieve import retrieve
from langgraph.graph.state import GraphState
from vectordb.pgvector import PGVectorDB
from config import Config
from langgraph.chains.retrieval_grader import retrieval_grader
from ingestor.confluence_connector  import ConfluenceConnector

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_retrieve():
    # Create a sample graph state
    conf_connector = ConfluenceConnector(
            Config.confluence_url,
            Config.confluence_username,
            Config.confluence_api_key
        )
    question = "What is Modamart?"
    graph_state = GraphState(
        question=question,
        generation=1,
        documents=[],
        nodes=[]
    )

    confluence_vector_db = PGVectorDB(Config.PGVECTOR_CONNECTION_STRING, "confluence")
    await confluence_vector_db.connect()

    # Call the retrieve function
    results = await retrieve(graph_state, confluence_vector_db)
    output = results.get('results')
    for doc in output:
        id = doc['external_id']
        content = conf_connector.fetch_page_by_id(id)['content']
        rg_output = retrieval_grader.invoke(
            {"question": question, "document": content}
        )
        print(rg_output)
        break
    await confluence_vector_db.close()
    
    

asyncio.run(test_retrieve())