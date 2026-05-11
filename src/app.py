import asyncio
import chainlit as cl
from rag_agents.confluence_assistant.conf_ass import conf_chain
from rag_agents.data_analysis.data_analyst import data_chain

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Define selectable agents/profiles
@cl.set_chat_profiles
async def get_chat_profiles():
    return [
        cl.ChatProfile(
            name="analysis_confluence",
            display_name="Analyst - Confluence",
            markdown_description="Search + summarize Confluence documents",
            icon="https://cdn-icons-png.flaticon.com/128/5968/5968793.png"
        ),
        cl.ChatProfile(
            name="analysis_data",
            display_name="Analyst - Data",
            markdown_description="SQL + analytics workflows",
            icon="https://cdn-icons-png.flaticon.com/128/2316/2316065.png"
        ),
        cl.ChatProfile(
            name="engineering_coding",
            display_name="Engineer - Coding",
            markdown_description="Code generation and debugging",
            icon="https://cdn-icons-png.flaticon.com/512/6062/6062646.png"
        )
    ]

@cl.on_chat_start
async def on_chat_start():
    profile = cl.user_session.get("chat_profile")
    # Initialize graph_state in session
    cl.user_session.set("graph_state", None)

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user messages and send responses."""
    profile = cl.user_session.get("chat_profile")
    graph_state = cl.user_session.get("graph_state")
    
    
    # CONFLUENCE ANALYST
    if profile == "analysis_confluence":
        response, state = await conf_chain(message.content, graph_state)

    # DATA ANALYST
    elif profile == "analysis_data":
        response, state = await data_chain(message.content, graph_state)
    
    # CODING AGENT
    elif profile == "engineering_coding":
        response = f"Engineering coding is not yet implemented."
        state = graph_state

    else:
        response = f"No valid agent selected for profile: {profile}."
        state = graph_state

    await cl.Message(content=response).send()
    cl.user_session.set("graph_state", state)