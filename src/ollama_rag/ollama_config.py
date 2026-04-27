import ollama
from config import Config

class OllamaEmbedder:
    def __init__(self, model=Config.ollama_model):
        self.model = model
    
    def embed_text(self, text):
        response = ollama.embed(
            model=self.model,
            input=text
        )
        return response.embeddings