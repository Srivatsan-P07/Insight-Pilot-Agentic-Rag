from rag_agents.confluence_assistant.graph.state import GraphState
from rag_agents.confluence_assistant.graph.graph import app

async def conf_chain(question: str, graph_state: GraphState = None) -> tuple[str, GraphState]:
    if graph_state is None:
        graph_state = GraphState(
            question=question,
            generation=None,
            documents=[],
            source='confluence'
        )
    graph_state = await app.ainvoke(input=graph_state)
    return graph_state['generation'], graph_state