import logging
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from config import Config, GCPConfig
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

class ChartSelectorResponse(BaseModel):
    """Response model for chart selection."""
    x_axis: Optional[str] = Field(
        default=None,
        description="The column to be used for the x-axis."
    )
    y_axis: Optional[str] = Field(
        default=None,
        description="The column to be used for the y-axis."
    )
    chart_type: Optional[str] = Field(
        default=None,
        description="The type of chart (Bar, Pie, or Line)."
    )

@lru_cache(maxsize=1)
def get_chart_selector():
    """
    Initializes and returns the chart selector chain.
    """
    structured_llm = GCPConfig.get_llm().with_structured_output(ChartSelectorResponse)

    system_instruction = (
        "You are a chart selection expert. Given the dataframe schema and user question, select:\n"
        "- x_axis: The column best suited for the x-axis\n"
        "- y_axis: The column best suited for the y-axis\n"
        "- chart_type: The most appropriate chart type (Bar, Pie, or Line)\n"
        "Return null only for fields you cannot determine from the provided context."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_instruction),
            ("human", "Columns: {columns}\nQuestion: {question}"),
        ]
    )

    logger.info("Chart selector chain initialized successfully.")
    chain = prompt | structured_llm
    return chain.with_config({"run_name": "chart_selector"})