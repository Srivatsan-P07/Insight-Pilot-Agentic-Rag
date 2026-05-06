import ollama
from config import Config
from langchain_ollama import ChatOllama

class OllamaObject:
    def __init__(self, model=Config.ollama_model):
        self.model = model
    
    def embed_text(self, text):
        response = ollama.embed(
            model=self.model,
            input=text
        )
        return response.embeddings
    
    def chatmodelinstance(self):
        return ChatOllama(model=Config.ollama_chat_model)