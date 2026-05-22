from rag_agents.data_analysis.graph.state import GraphState
from rag_agents.data_analysis.graph.graph import app
from typing import Tuple, Optional
import chainlit as cl
import plotly.express as px
from tracing import trace_chain

@trace_chain("data_chain")
async def data_chain(question: str, graph_state: Optional[GraphState] = None) -> Tuple[str, GraphState]:
    # Initialize graph state if not provided
    graph_state = GraphState(
        question=question,
        generation=None,
        schemas=[]
    )

    # Invoke the graph and get the updated state
    graph_state = GraphState(**await app.ainvoke(graph_state))

    # Extract chart configuration
    chart_type = graph_state.chart_config.get("type").lower()

    # Define chart functions with configurations
    chart_map = {
        "bar": px.bar,
        "line": px.line,
        "pie": px.pie
    }
    
    if chart_type not in chart_map:
        return graph_state

    # Generate and display chart
    x_axis = graph_state.chart_config.get("x")
    y_axis = graph_state.chart_config.get("y")
    
    if chart_type == "pie":
        fig = px.pie(graph_state.execution, names=x_axis, values=y_axis, title=f"{x_axis} Distribution")
    else:
        fig = chart_map[chart_type](graph_state.execution, x=x_axis, y=y_axis, title=f"{y_axis} by {x_axis}")
    
    graph_state.plotly = [cl.Plotly(name="dynamic_chart", figure=fig, display="inline")]

    return graph_state