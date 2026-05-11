from pydantic import BaseModel
from typing import List, Optional, Any

class GraphState(BaseModel):
    question: str
    chat_history: List[Any]
    generation: Optional[str] = None
    schemas: List[str]
    source: str = "dataplex"