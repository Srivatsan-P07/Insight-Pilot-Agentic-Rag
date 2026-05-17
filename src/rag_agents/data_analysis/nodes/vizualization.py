from rag_agents.data_analysis.graph.state import GraphState
from rag_agents.data_analysis.chains.chart_grader import get_chart_selector
from config import Config, GCPConfig
import logging

logger = logging.getLogger(__name__)


async def chart_selector_node(state: GraphState):
    """Select appropriate chart type based on data characteristics."""
    question = state.question
    schema = state.schemas
    columns = state.execution.columns.tolist() if state.execution is not None else []
    
    chain = get_chart_selector()
    selected_columns = chain.invoke({"question": question, "schema": schema, "columns": columns})
    print(selected_columns)
    
    state.chart_config = {
        "type": selected_columns.chart_type if selected_columns.chart_type in ["Bar", "Pie", "Line"] else "table",
        "x": selected_columns.x_axis,
        "y": selected_columns.y_axis,
    }

    return state