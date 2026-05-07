import asyncio
from rag_agents.confluence_assistant.graph.state import GraphState
from rag_agents.confluence_assistant.graph.graph import app
import chainlit as cl

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



# Define selectable agents/profiles
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="research_agent",
            display_name="Research Agent",
            markdown_description="Search + summarize documents",
            icon="https://cdn-icons-png.flaticon.com/512/4712/4712109.png",
        ),
        cl.ChatProfile(
            name="coding_agent",
            display_name="Coding Agent",
            markdown_description="Code generation and debugging",
            icon="https://cdn-icons-png.flaticon.com/512/6062/6062646.png",
        ),
        cl.ChatProfile(
            name="data_agent",
            display_name="Data Analyst",
            markdown_description="SQL + analytics workflows",
            icon="https://cdn-icons-png.flaticon.com/512/2103/2103633.png",
        ),
    ]

@cl.on_chat_start
async def on_chat_start():
    chat_profile = cl.user_session.get("chat_profile")
    await cl.Message(
        content=f"starting chat using the {chat_profile} chat profile"
    ).send()

async def tools_agent(question: str) -> str:
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
    chat_profile = cl.user_session.get("chat_profile")
    
    # RESEARCH AGENT
    if chat_profile == "research_agent":
        response = await tools_agent(message.content)

    # CODING AGENT
    elif chat_profile == "coding_agent":
        response = f"Coding Agent received: {message.content}"

    # DATA AGENT
    elif chat_profile == "data_agent":
        response = f"Data Agent received: {message.content}"

    else:
        response = "No valid agent selected."

    await cl.Message(content=response).send()