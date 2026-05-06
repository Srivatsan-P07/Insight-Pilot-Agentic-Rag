from langgraph.graph import END, StateGraph

from agents.insight_pilot.langgraph_rag.graph.consts import RETRIEVE, GRADE_DOCUMENTS, GENERATE
from agents.insight_pilot.langgraph_rag.graph.state import GraphState
from agents.insight_pilot.langgraph_rag.nodes.retrieve import retrieve
from agents.insight_pilot.langgraph_rag.nodes.grade_documents import gradedocuments
from agents.insight_pilot.langgraph_rag.nodes.generate import generate

# Initialize WorkFlow
workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_DOCUMENTS, gradedocuments)
workflow.add_node(GENERATE, generate)

# EntryPoint & Edges
workflow.set_entry_point(RETRIEVE)
workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)
workflow.add_edge(GRADE_DOCUMENTS, GENERATE)
workflow.add_edge(GENERATE, END)

# Compile
app = workflow.compile()

app.get_graph().draw_mermaid_png(output_file_path='graph.png')