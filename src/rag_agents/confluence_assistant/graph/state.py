from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class GraphState:
    question: str
    generation: Optional[int] = None
    documents: List[str] = field(default_factory=list)
    source: str = "confluence"