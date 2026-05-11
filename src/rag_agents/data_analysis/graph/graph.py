from langgraph.graph import END, StateGraph
from rag_agents.data_analysis.graph.consts import RETRIEVE, GRADE_SCHEMAS, GENERATE_SQL
from rag_agents.data_analysis.graph.state import GraphState
from rag_agents.data_analysis.nodes.retrieve import retrieve
from rag_agents.data_analysis.nodes.grade_schemas import gradeschemas
from rag_agents.data_analysis.nodes.generate import generate

# Initialize WorkFlow
workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_SCHEMAS, gradeschemas)
workflow.add_node(GENERATE_SQL, generate)

# EntryPoint & Edges
workflow.set_entry_point(RETRIEVE)
workflow.add_edge(RETRIEVE, GRADE_SCHEMAS)
workflow.add_edge(GRADE_SCHEMAS, GENERATE_SQL)
workflow.add_edge(GENERATE_SQL, END)

# Compile
app = workflow.compile()

app.get_graph().draw_mermaid_png(output_file_path='graph.png')