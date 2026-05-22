import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from config import Config, GCPConfig
from functools import lru_cache

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_generation_chain():
    """
    Initializes and returns the generation chain for the RAG pipeline.
    """
    try:
        # Define Prompt
        system_instruction = (
            "You are a helpful assistant. "
            "Use the following context to answer the question. If you don't know, say you don't know. "
            "Keep your answers short and crisp. "
            "Answer in bullet points and in a structured way."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_instruction),
                MessagesPlaceholder(variable_name="chat_history"),
                (
                    "human",
                    "Context:\n{context}\n\n"
                    "Question:\n{question}\n\n"
                    "Answer:"
                ),
            ]
        )

        # Build Chain
        chain = prompt | GCPConfig.get_llm() | StrOutputParser()
        chain = chain.with_config({"run_name": "document_summarizer"})
        
        logger.info("Generation chain successfully initialized.")
        return chain

    except Exception as e:
        logger.error(f"Failed to initialize generation chain: {str(e)}")
        raise