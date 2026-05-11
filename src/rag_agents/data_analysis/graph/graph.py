from langgraph.graph import END, StateGraph
from rag_agents.data_analysis.graph.consts import RETRIEVE, GRADE_SCHEMAS, GENERATE_SQL, EXECUTE_SQL
from rag_agents.data_analysis.graph.state import GraphState
from rag_agents.data_analysis.nodes.retrieve import retrieve
from rag_agents.data_analysis.nodes.grade_schemas import gradeschemas
from rag_agents.data_analysis.nodes.generate_sql import generate_sql
from rag_agents.data_analysis.nodes.execute_sql import execute_sql

# Initialize WorkFlow
workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_SCHEMAS, gradeschemas)
workflow.add_node(GENERATE_SQL, generate_sql)
workflow.add_node(EXECUTE_SQL, execute_sql)

# EntryPoint & Edges
workflow.set_entry_point(RETRIEVE)
workflow.add_edge(RETRIEVE, GRADE_SCHEMAS)
workflow.add_edge(GRADE_SCHEMAS, GENERATE_SQL)
workflow.add_edge(GENERATE_SQL, EXECUTE_SQL)
workflow.add_edge(EXECUTE_SQL, END)

# Compile
app = workflow.compile()