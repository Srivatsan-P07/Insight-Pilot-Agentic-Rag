from rag_agents.confluence_assistant.graph.state import GraphState
from rag_agents.confluence_assistant.graph.graph import app

async def conf_chain(question: str, graph_state: GraphState = None) -> tuple[str, GraphState]:
    print(graph_state)
    graph_state = graph_state or GraphState(
        question=question,
        generation=None,
        documents=[],
        source='confluence'
    )
    graph_state.question = question
    graph_state = await app.ainvoke(input=graph_state)
    return graph_state['generation'], graph_state