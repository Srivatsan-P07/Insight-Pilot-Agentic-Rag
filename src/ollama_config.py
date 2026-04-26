import ollama
from config import Config

class OllamaEmbedder:
    def __init__(self, host=Config.ollama_host, model=Config.ollama_model):
        self.client = ollama.Client(host=host)
        self.model = model
    
    def embed(self, text):
        response = self.client.embed(
            model=self.model,
            input=text
        )
        return response.embeddings