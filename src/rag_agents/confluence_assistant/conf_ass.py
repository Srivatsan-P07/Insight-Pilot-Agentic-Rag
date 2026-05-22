from rag_agents.confluence_assistant.graph.state import GraphState
from rag_agents.confluence_assistant.graph.graph import app
from langchain_core.messages import HumanMessage, AIMessage
from typing import Tuple, Optional
from tracing import trace_chain

@trace_chain("confluence_chain")
async def conf_chain(question: str, graph_state: Optional[GraphState] = None) -> Tuple[str, GraphState]:
    if graph_state is None:
        graph_state = GraphState(
            chat_history=[],
            question=question,
            generation=None,
            documents=[],
            source='confluence'
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
    
    return output_state.generation, output_state