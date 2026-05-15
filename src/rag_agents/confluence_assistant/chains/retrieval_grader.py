import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from config import GCPConfig

# Configure logging
logger = logging.getLogger(__name__)

class GradeResponse(BaseModel):
    """Binary score for document relevance assessment."""
    binary_score: str = Field(
        description="Relevance score: 'yes' if the document is relevant to the question, otherwise 'no'."
    )

def create_retrieval_grader():
    """
    Initializes and returns the retrieval grader chain.
    """
    llm = GCPConfig.llm

    # Bind structured output to the LLM
    structured_llm_grader = llm.with_structured_output(GradeResponse)

    system_instruction = (
        "You are a grader assessing relevance of a retrieved document to a user question.\n"
        "If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant.\n"
        "Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the question."
    )

    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_instruction),
            ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
        ]
    )

    logger.info("Retrieval grader chain successfully initialized.")
    return grade_prompt | structured_llm_grader

# Singleton instance for the application
retrieval_grader = create_retrieval_grader()