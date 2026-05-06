import asyncio
from rag_agents.confluence_assistant.graph.state import GraphState
from rag_agents.confluence_assistant.graph.graph import app
import chainlit as cl

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@cl.step(type="tool")
async def tool(question: str) -> str:
    graph_state = GraphState(
        question=question,
        generation=None,
        documents=[],
        source='confluence'
    )
    graph_state_dict = await app.ainvoke(input=graph_state)
    return (graph_state_dict.get("generation") or "No answer generated.")

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user messages and send responses."""
    text = await tool(message.content)
    await cl.Message(content=text).send()