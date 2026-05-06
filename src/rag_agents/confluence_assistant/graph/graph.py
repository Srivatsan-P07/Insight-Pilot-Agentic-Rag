from langgraph.graph import END, StateGraph

from rag_agents.confluence_assistant.graph.consts import RETRIEVE, GRADE_DOCUMENTS, GENERATE
from rag_agents.confluence_assistant.graph.state import GraphState
from rag_agents.confluence_assistant.nodes.retrieve import retrieve
from rag_agents.confluence_assistant.nodes.grade_documents import gradedocuments
from rag_agents.confluence_assistant.nodes.generate import generate

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