import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    # Ollama Configuration
    ollama_host = "http://localhost:11434"
    ollama_model = "nomic-embed-text-v2-moe"
    ollama_chat_model = "llama3:8b"
    #ollama_chat_model = "mistral:7b"
    
    # Confluence Configuration
    confluence_url = "https://vatsan-7.atlassian.net/wiki"
    confluence_username = "svs.vatsan7@gmail.com"
    confluence_api_key = os.getenv("CONFLUENCE_API_KEY")
    confluence_space_key = "modamart"

    # sample testing localhost
    PGVECTOR_CONNECTION_STRING = "postgresql://user:password@localhost:5432/vectordb"