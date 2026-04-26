from langchain_community.document_loaders import ConfluenceLoader
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

class ConfluenceIngestor:
    def __init__(self, url: str, username: str, api_key: str):
        self.url = url
        self.username = username
        self.api_key = api_key

    def load_documents(self, space_key: str):
        loader = ConfluenceLoader(
            url = self.url,
            username = self.username,
            api_key = self.api_key,
            space_key = space_key

            #include_attachments=True,
            #limit=50,
        )
        documents = loader.load()
        return documents