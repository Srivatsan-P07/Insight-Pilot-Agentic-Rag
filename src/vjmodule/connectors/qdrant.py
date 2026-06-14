from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import Config


class QdrantConnector:
  def __init__(self, host: str = "localhost", port: int = 6333, api_key: Optional[str] = None):
    """Initialize Qdrant client connection"""
    self.client = QdrantClient(host=host, port=port, api_key=api_key)
  
  def get_embedding(self, text: str) -> List[float]:
    """Get embedding from GoogleGenerativeAIEmbeddings"""
    try:
      embedding = Config.embeddings.embed_query(text)
      return embedding
    except Exception as e:
      raise Exception(f"Error generating embedding: {e}")
    
  def get_collection(self, collection_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve collection information."""
    try:
      info = self.client.get_collection(collection_name)
      return info.dict()
    except Exception as e:
      raise Exception(f"Error retrieving collection: {e}")
  
  def create_collection(self, collection_name: str, vector_size: int = 768, distance_metric: str = "Cosine") -> bool:
    """Create a new collection in Qdrant."""
    try:
      self.client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance[distance_metric.upper()]),
      )
      return True
    except Exception as e:
      raise Exception(f"Error creating collection: {e}")
  
  def store_points(self, collection_name: str, points: List[PointStruct]) -> bool:
    """Store vectors with payloads in collection."""
    try:
      self.client.upsert(collection_name=collection_name, points=points)
      return True
    except Exception as e:
      raise Exception(f"Error storing points: {e}")
    
  def similarity_search(self, collection_name: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Perform similarity search and return results."""
    try:
      query_embedding = self.get_embedding(query)
      if not query_embedding:
        raise Exception("Failed to generate embedding for query.")
      
      search_result = self.client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        limit=top_k
      )
      results_as_dict = [
        {
          "id": hit.id,
          "score": hit.score,
          "payload": hit.payload
        }
        for hit in search_result.points
      ]
      return results_as_dict
    except Exception as e:
      raise Exception(f"Error performing similarity search: {e}")