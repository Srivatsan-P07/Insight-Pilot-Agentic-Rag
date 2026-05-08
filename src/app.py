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
    profile = cl.user_session.get("chat_profile")
    await cl.Message(
        content=f"starting chat using the {profile} chat profile"
    ).send()
    # Initialize graph_state in session
    cl.user_session.set("graph_state", None)

async def tools_agent(question: str, graph_state: GraphState = None) -> str:
    if graph_state is None:
        graph_state = GraphState(
            question=question,
            generation=None,
            documents=[],
            source='confluence'
        )
    else:
        # Update question while preserving history
        graph_state.question = question
    
    graph_state = await app.ainvoke(input=graph_state)
    return (graph_state['generation'], graph_state)

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user messages and send responses."""
    profile = cl.user_session.get("chat_profile")
    graph_state = cl.user_session.get("graph_state")
    
    
    # RESEARCH AGENT
    if profile == "research_agent":
        response, state = await tools_agent(message.content, graph_state)

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