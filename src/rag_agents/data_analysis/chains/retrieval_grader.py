import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from config import Config, GCPConfig

# Configure logging
logger = logging.getLogger(__name__)

class GradeResponse(BaseModel):
    """Binary score for schema relevance assessment."""
    binary_score: str = Field(
        description="Relevance score: 'yes' if the schema is relevant to the question, otherwise 'no'."
    )

def create_retrieval_grader():
    """
    Initializes and returns the retrieval grader chain.
    """
    

    # Bind structured output to the LLM
    structured_llm_grader = GCPConfig.get_llm().with_structured_output(GradeResponse)

    system_instruction = (
        "You are an expert data grader evaluating the relevance of a retrieved database schema to a user's question.\n"
        "Determine if the schema provides the necessary tables or columns required to construct a valid SQL query for the question.\n"
        "Respond with a binary score: 'yes' if the schema is relevant, or 'no' if it is not."
    )

    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_instruction),
            ("human", "Retrieved schemas: \n\n {schemas} \n\n User question: {question}"),
        ]
    )

    logger.info("Retrieval grader chain successfully initialized.")
    chain = grade_prompt | structured_llm_grader
    return chain.with_config({"run_name": "schema_grader"})

# Singleton instance for the application
retrieval_grader = create_retrieval_grader()