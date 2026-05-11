import logging
from typing import Any, Dict
from ingestor.bigquery_connector import BigQueryConnector
from config import Config

from rag_agents.data_analysis.graph.state import GraphState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_sql(graph_state: GraphState) -> GraphState:
    question = graph_state.question
    schemas = graph_state.schemas
    chat_history = graph_state.chat_history

    logger.info(f"Executing SQL for question: {question}")
    bq_client = BigQueryConnector(project_id=Config.GCP_PROJECT_ID)
    # remove first and last line of the generated SQL if they are code block markers
    if graph_state.generation.startswith("```sql") and graph_state.generation.endswith("```"):
        graph_state.generation = graph_state.generation[6:-3].strip()
    
    
    execution = bq_client.query(graph_state.generation)
    logger.info("Execution completed.")
    graph_state.execution = execution

    return graph_state