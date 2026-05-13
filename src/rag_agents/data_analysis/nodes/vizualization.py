from rag_agents.data_analysis.graph.state import GraphState
from rag_agents.data_analysis.chains.chart_grader import chart_selector

async def chart_selector_node(state: GraphState):
    """Select appropriate chart type based on data characteristics."""
    question = state.question
    schema = state.schemas
    columns = state.execution.columns.tolist() if state.execution is not None else []
    selected_columns = chart_selector.invoke({"question": question, "schema": schema, "columns": columns})
    
    if selected_columns.x_axis == 'null' or selected_columns.y_axis == 'null' or selected_columns.chart_type == 'null':
        state.chart_config = {"type": "table"}
    else:
        state.chart_config = {
            "type": selected_columns.chart_type,
            "x": selected_columns.x_axis,
            "y": selected_columns.y_axis,
        }

    return state