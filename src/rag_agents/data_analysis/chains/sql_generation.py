import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from config import Config, GCPConfig, AppLogger, llm

logger = AppLogger.setup()

def create_generation_chain():
    """
    Initializes and returns the generation chain for the RAG pipeline.
    """
    try:
        # Initialize LLM
        

        # Define Prompt
        system_instruction = (
            "You are an expert BigQuery SQL developer. Generate accurate, optimized SQL queries based on the provided schema.\n"
            "Only use tables and columns from the given schema. If the query cannot be constructed from the available schema, clearly state that.\n"
            "Ensure queries are efficient, properly formatted, and follow BigQuery best practices.\n"
            "Only give the SQL query as the answer without any additional text or explanation."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_instruction),
                (
                    "human",
                    "Schemas:\n{schemas}\n\n"
                    "Question:\n{question}\n\n"
                    "Answer:"
                ),
            ]
        )

        # Build Chain
        chain = prompt | llm | StrOutputParser()
        
        logger.app("Generation chain successfully initialized.")
        return chain

    except Exception as e:
        logger.error(f"Failed to initialize generation chain: {str(e)}")
        raise

# Singleton instance for the application
generation_chain = create_generation_chain()