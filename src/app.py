import asyncio
import chainlit as cl
from rag_agents.confluence_assistant.conf_ass import conf_chain

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



# Define selectable agents/profiles
@cl.set_chat_profiles
def chat_profile():
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
    profile = cl.user_session.get("chat_profile")
    await cl.Message(
        content=f"starting chat using the {profile} chat profile"
    ).send()
    # Initialize graph_state in session
    cl.user_session.set("graph_state", None)

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user messages and send responses."""
    profile = cl.user_session.get("chat_profile")
    graph_state = cl.user_session.get("graph_state")
    
    
    # RESEARCH AGENT
    if profile == "research_agent":
        response, state = await conf_chain(message.content, graph_state)

    # CODING AGENT
    elif profile == "coding_agent":
        response = f"Coding Agent received: {message.content}"
        state = graph_state

    # DATA AGENT
    elif profile == "data_agent":
        response = f"Data Agent received: {message.content}"
        state = graph_state

    else:
        response = "No valid agent selected."
        state = graph_state

    await cl.Message(content=response).send()
    cl.user_session.set("graph_state", state)