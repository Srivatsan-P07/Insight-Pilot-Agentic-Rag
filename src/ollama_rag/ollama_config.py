import ollama
from config import Config
from langchain_ollama import ChatOllama
from langchain.chat_models import init_chat_model

class OllamaObject:
    def __init__(self, model=Config.OLLAMA_MODEL):
        self.model = model
    
    def embed_text(self, text):
        response = ollama.embed(
            model=self.model,
            input=text
        )
        return response.embeddings
    
    def chatmodelinstance(self):
        return Config.llm
        """
        return init_chat_model(
            model=Config.OLLAMA_CHAT_MODEL,
            provider=Config.OLLAMA_MODEL_PROVIDER
        )
        """