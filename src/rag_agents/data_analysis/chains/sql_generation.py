import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from ollama_rag.ollama_config import OllamaObject

logger = logging.getLogger(__name__)

def create_generation_chain():
    """
    Initializes and returns the generation chain for the RAG pipeline.
    """
    try:
        # Initialize LLM
        ollama_model = OllamaObject()
        llm = ollama_model.chatmodelinstance()

        # Define Prompt
        system_instruction = (
            "You are an expert BigQuery SQL developer. Generate accurate, optimized SQL queries based on the provided schema. "
            "Only use tables and columns from the given schema. If the query cannot be constructed from the available schema, clearly state that. "
            "Ensure queries are efficient, properly formatted, and follow BigQuery best practices."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_instruction),
                MessagesPlaceholder(variable_name="chat_history"),
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
        
        logger.info("Generation chain successfully initialized.")
        return chain

    except Exception as e:
        logger.error(f"Failed to initialize generation chain: {str(e)}")
        raise

# Singleton instance for the application
generation_chain = create_generation_chain()