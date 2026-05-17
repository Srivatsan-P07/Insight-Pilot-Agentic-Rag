from typing import List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from config import Config, GCPConfig
from functools import lru_cache
import logging

# Configure logging
logger = logging.getLogger(__name__)

class GradeResponse(BaseModel):
    document_id: int = Field(description="The numeric ID/index of the document as provided in the prompt")
    is_relevant: bool = Field(description="True if the document is relevant to the question, otherwise False.")

class BatchGradeResponse(BaseModel):
    """Batch assessment of multiple documents."""
    results: List[GradeResponse] = Field(description="List of grading results for the provided documents.")

@lru_cache(maxsize=1)
def get_retrieval_grader():
    # Bind structured output to the LLM
    structured_llm_grader = GCPConfig.get_llm().with_structured_output(BatchGradeResponse)

    system_instruction = (
        "You are a grader assessing relevance of retrieved documents to a user question.\n"
        "If a document contains keyword(s) or semantic meaning related to the question, grade it as relevant.\n"
        "Assess ALL provided documents and return a list of relevance scores."
    )

    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_instruction),
            ("human", "Retrieved documents: \n\n {documents} \n\n User question: {question}"),
        ]
    )

    logger.info("Retrieval grader chain successfully initialized.")
    return grade_prompt | structured_llm_grader