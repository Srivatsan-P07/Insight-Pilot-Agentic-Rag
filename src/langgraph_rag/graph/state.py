from typing import List, TypedDict

class GraphState(TypedDict):
    """
    Represents the state of our graph,

    Attributes:
        question: The original question that the graph is trying to answer.
        generation: The current generation of the graph, which can be used to track the progress of the graph construction.
        documents: A list of documents that have been retrieved and are relevant to the question.
    """
    
    question: str
    generation: int
    documents: List[str]
    source: str