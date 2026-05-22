import logging
from typing import Any, Dict
from ingestor.bigquery_connector import BigQueryConnector
from config import Config, GCPConfig

from rag_agents.data_analysis.graph.state import GraphState
from tracing import trace_node

logger = logging.getLogger(__name__)

@trace_node("execute_sql")
def execute_sql(graph_state: GraphState) -> GraphState:
    question = graph_state.question
    schemas = graph_state.schemas

    logger.info(f"Executing SQL for question: {question}")
    bq_client = BigQueryConnector(project_id=GCPConfig.GCP_PROJECT_ID)
    # remove first and last line of the generated SQL if they are code block markers
    if graph_state.generation.startswith("```sql") and graph_state.generation.endswith("```"):
        graph_state.generation = graph_state.generation[6:-3].strip()
    
    
    execution = bq_client.query(graph_state.generation)
    logger.info("Execution completed.")
    graph_state.execution = execution

    return graph_state