import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class Config:
    # Ollama
    OLLAMA_HOST = "http://localhost:11434"
    OLLAMA_MODEL = "nomic-embed-text-v2-moe"
    OLLAMA_CHAT_MODEL = "google_genai:gemini-2.0-flash"
    OLLAMA_MODEL_PROVIDER = "google_genai"

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

    # GCP & LLM
    GCP_PROJECT_ID = "insight-pilot-trios"
    GCP_REGION = "us-central1"
    CHAT_MODEL = "gemini-2.5-flash"

    _llm_config = {
        "project": GCP_PROJECT_ID,
        "location": GCP_REGION,
        "vertexai": True,
    }

    llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, **_llm_config)