import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import ollama
from langchain_ollama import ChatOllama
from langchain.chat_models import init_chat_model
import logging

load_dotenv()

class AppLogger:
    APP_LOG_LEVEL = 25  # Between INFO (20) and WARNING (30)

    @staticmethod
    def setup():
        # Add custom level if it doesn't exist
        if not hasattr(logging, "APP"):
            logging.addLevelName(AppLogger.APP_LOG_LEVEL, "APP")
            def app_log(self, message, *args, **kwargs):
                if self.isEnabledFor(AppLogger.APP_LOG_LEVEL):
                    self._log(AppLogger.APP_LOG_LEVEL, message, args, **kwargs)
            logging.Logger.app = app_log

        # Configure root logger to silence 3rd parties
        logging.basicConfig(level=logging.WARNING)
        
        # Silence specific noisy libraries
        for lib in ["urllib3", "google", "httpx", "vertexai", "langchain"]:
            logging.getLogger(lib).setLevel(logging.WARNING)

        # Create and configure the app-specific logger
        logger = logging.getLogger("my_app")
        logger.setLevel(AppLogger.APP_LOG_LEVEL)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        logger.propagate = False
        return logger

class Config:
    # Confluence
    CONFLUENCE_URL = "https://vatsan-7.atlassian.net/wiki"
    CONFLUENCE_USERNAME = "svs.vatsan7@gmail.com"
    CONFLUENCE_API_KEY = os.getenv("CONFLUENCE_API_KEY")
    CONFLUENCE_SPACE_KEY = "modamart"

    # Database
    PGVECTOR_CONNECTION_STRING = os.getenv(
        "PGVECTOR_CONNECTION_STRING",
        "postgresql://user:password@localhost:5432/vectordb"
    )

class OllamaObject:
    OLLAMA_HOST = "http://localhost:11434"
    OLLAMA_MODEL = "nomic-embed-text-v2-moe"
    OLLAMA_CHAT_MODEL = "llama3:8b" # Or your preferred chat model

    def __init__(self, model=OLLAMA_MODEL):
        self.model = model
    
    def embed_query(self, text):
        response = ollama.embed(model=self.model, input=text)
        return response.embeddings
        
class GCPConfig:
    # GCP Settings
    GCP_PROJECT_ID = "insight-pilot-trios"
    GCP_REGION = "us-central1"
    CHAT_MODEL = "gemini-2.5-flash"
    EMBEDDING_MODEL = "text-embedding-004"
    TASK_TYPE = "retrieval_document"
    OUTPUT_DIMENSIONALITY = 768
    
    # Provider Toggle: "google" or "ollama"
    PROVIDER = "google" 
    ollama_object = OllamaObject()
    

    @classmethod
    def get_llm(cls):
        os.environ["GOOGLE_CLOUD_PROJECT"] = cls.GCP_PROJECT_ID
        if cls.PROVIDER == "google":
            return ChatGoogleGenerativeAI(
                model=cls.CHAT_MODEL,
                project=cls.GCP_PROJECT_ID,
                location=cls.GCP_REGION,
                vertexai=True,
            )
        else:
            return init_chat_model(
                model=cls.ollama_object.OLLAMA_CHAT_MODEL,
                model_provider="ollama"
            )

    @classmethod
    def get_embedding_model(cls):
        if cls.PROVIDER == "google":
            return GoogleGenerativeAIEmbeddings(
                model=cls.EMBEDDING_MODEL,
                task_type=cls.TASK_TYPE,
                output_dimensionality=cls.OUTPUT_DIMENSIONALITY,
                project=cls.GCP_PROJECT_ID,
                location=cls.GCP_REGION,
                vertexai=True,
            )
        else:
            return cls.ollama_object

# Initialize instances outside the class for easy import
GCPConfig.llm = GCPConfig.get_llm()
GCPConfig.embedding_model = GCPConfig.get_embedding_model()
llm = GCPConfig.llm
embedding_model = GCPConfig.embedding_model