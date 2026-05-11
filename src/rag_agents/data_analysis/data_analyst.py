from rag_agents.data_analysis.graph.state import GraphState
from rag_agents.data_analysis.graph.graph import app
from langchain_core.messages import HumanMessage, AIMessage
from typing import Tuple, Optional


async def data_chain(question: str, graph_state: Optional[GraphState] = None) -> Tuple[str, GraphState]:
    if graph_state is None:
        graph_state = GraphState(
            question=question,
            chat_history=[],
            generation=None,
            schemas=[],
            source='dataplex'
        )
    else:
        graph_state.question = question

    # Invoke the graph and get the updated state
    output_state = GraphState(**await app.ainvoke(graph_state))
    
    # Update chat history with the new exchange
    output_state.chat_history.extend(
        [HumanMessage(content=question),
        AIMessage(content=output_state.generation)]
    )
    
    return output_state.generation, output_state.execution, output_state