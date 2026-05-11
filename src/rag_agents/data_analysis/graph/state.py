from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
import pandas as pd


class GraphState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    question: str
    chat_history: List[Any]
    generation: Optional[str] = None
    execution: Optional[pd.DataFrame] = None
    schemas: List[dict]
    source: str = "dataplex"