import asyncio
import chainlit as cl
from rag_agents.confluence_assistant.conf_ass import conf_chain
from rag_agents.data_analysis.data_analyst import data_chain
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    graph_state = None
    output = await data_chain("Summarize modamart sales", graph_state)
    print(output)
    
asyncio.run(main())