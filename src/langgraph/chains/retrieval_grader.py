from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from ollama_rag.ollama_config import OllamaEmbedder

ollama_model = OllamaEmbedder()

class RetrievalGrader(BaseModel):
    """ Binary Score to check if the retrieved document is relevant to the question. """
    binary_score: str = Field(
        description="Binary score to check if the retrieved document is relevant to the question. Should be either 'yes' or 'no'."
    )

llm = ollama_model.chatmodelinstance()

structured_llm_grader = llm.with_structured_output(RetrievalGrader)

system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader