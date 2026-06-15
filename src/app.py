import asyncio
import chainlit as cl

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.langchain import LangChainInstrumentor

# Configure OpenTelemetry to send traces to Phoenix via HTTP
endpoint = "http://localhost:6006/v1/traces"
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint)))
trace.set_tracer_provider(tracer_provider)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

from rag_agents.confluence_assistant.conf_ass import conf_chain
from rag_agents.data_analysis.data_analyst import data_chain
from config import AppLogger, GCPConfig
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache

from vjmodule.agents.gcp_cost_agent import stream_cost_analysis
from vjmodule.agents.gcp_recommender_agent import stream_recommendations
from vjmodule.agents.github_agent import stream_github_analysis
from vjmodule.agents.code_optimizer_agent import stream_code_optimization

AppLogger.setup()
set_llm_cache(InMemoryCache())
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Define selectable agents/profiles
@cl.set_chat_profiles
async def get_chat_profiles():
    return [
        cl.ChatProfile(
            name="analysis_confluence",
            display_name="[Analytics] Docs Assistant",
            markdown_description="Search + summarize Confluence documents",
            icon="https://cdn-icons-png.flaticon.com/128/5968/5968793.png"
        ),
        cl.ChatProfile(
            name="analysis_data",
            display_name="[Analytics] SQL Analytics",
            markdown_description="SQL + analytics workflows in BigQuery",
            icon="https://cdn-icons-png.flaticon.com/128/2316/2316065.png"
        ),
        cl.ChatProfile(
            name="gcp_cost",
            display_name="[Infra] GCP Cost Analyser",
            markdown_description="Full-stack cost visibility across GCP services",
            icon="https://cdn-icons-png.flaticon.com/512/3135/3135706.png"
        ),
        cl.ChatProfile(
            name="gcp_recommender",
            display_name="[Infra] GCP Recommender",
            markdown_description="Automated optimisation suggestions with savings",
            icon="https://cdn-icons-png.flaticon.com/512/4233/4233830.png"
        ),
        cl.ChatProfile(
            name="github",
            display_name="[DevTools] GitHub Integration",
            markdown_description="PR & Commit Analysis",
            icon="https://cdn-icons-png.flaticon.com/512/733/733609.png"
        ),
        cl.ChatProfile(
            name="code_optimizer",
            display_name="[DevTools] Code Cost Optimizer",
            markdown_description="Detect cost inefficiencies or performance issues",
            icon="https://cdn-icons-png.flaticon.com/512/1006/1006509.png"
        )
    ]

@cl.set_starters
async def set_starters(chat_profile: str):
    if chat_profile == "analysis_confluence":
        return [
            cl.Starter(
                label="Search Architecture Docs",
                message="Are there any documents detailing the application's overall system architecture or database schemas?",
                icon="https://cdn-icons-png.flaticon.com/128/5968/5968793.png"
            ),
            cl.Starter(
                label="Search Deployment Steps",
                message="What are the standard steps for deploying this project to a production environment?",
                icon="https://cdn-icons-png.flaticon.com/128/5968/5968793.png"
            )
        ]
    elif chat_profile == "analysis_data":
        return [
            cl.Starter(
                label="Top Selling Products",
                message="What were the top 10 selling products last quarter?",
                icon="https://cdn-icons-png.flaticon.com/128/2316/2316065.png"
            ),
            cl.Starter(
                label="Monthly Active Users",
                message="Show me the monthly active user count for the past 6 months",
                icon="https://cdn-icons-png.flaticon.com/128/2316/2316065.png"
            )
        ]
    elif chat_profile == "gcp_cost":
        return [
            cl.Starter(
                label="Cost Drivers",
                message="What are my top 5 cost drivers this month?",
                icon="https://cdn-icons-png.flaticon.com/512/3135/3135706.png"
            ),
            cl.Starter(
                label="Cost Spikes",
                message="Show me any cost spikes in the last 30 days.",
                icon="https://cdn-icons-png.flaticon.com/512/3135/3135706.png"
            )
        ]
    elif chat_profile == "gcp_recommender":
        return [
            cl.Starter(
                label="GCP Optimisations",
                message="Show all active recommendations with savings estimates",
                icon="https://cdn-icons-png.flaticon.com/512/4233/4233830.png"
            ),
            cl.Starter(
                label="Idle VM Savings",
                message="Explain idle VM savings opportunities",
                icon="https://cdn-icons-png.flaticon.com/512/4233/4233830.png"
            )
        ]
    elif chat_profile == "github":
        return [
            cl.Starter(
                label="Summarize Open PRs",
                message="Summarise the 5 most recent open PRs",
                icon="https://cdn-icons-png.flaticon.com/512/733/733609.png"
            ),
            cl.Starter(
                label="Recent Commits",
                message="What changed in the last 10 commits?",
                icon="https://cdn-icons-png.flaticon.com/512/733/733609.png"
            )
        ]
    elif chat_profile == "code_optimizer":
        return [
            cl.Starter(
                label="Explain Idle VM Cost",
                message="How can I optimize my code to avoid idle resources?",
                icon="https://cdn-icons-png.flaticon.com/512/1006/1006509.png"
            ),
            cl.Starter(
                label="Find Performance Bottlenecks",
                message="Check this project's code for potential performance improvements",
                icon="https://cdn-icons-png.flaticon.com/512/1006/1006509.png"
            )
        ]
    return []

@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("project_id", settings.get("project_id", GCPConfig.GCP_PROJECT_ID))
    cl.user_session.set("github_repo", settings.get("github_repo", ""))

@cl.on_chat_start
async def on_chat_start():
    profile = cl.user_session.get("chat_profile")
    cl.user_session.set("graph_state", None)

    # Setup chat settings for project_id and github_repo
    settings = cl.ChatSettings(
        [
            cl.input_widget.TextInput(
                id="project_id",
                label="GCP Project ID",
                initial=GCPConfig.GCP_PROJECT_ID,
            ),
            cl.input_widget.TextInput(
                id="github_repo",
                label="GitHub Repository (owner/repo)",
                initial="",
            ),
        ]
    )
    await settings.send()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming user messages and send responses."""
    profile = cl.user_session.get("chat_profile")
    graph_state = cl.user_session.get("graph_state")
    
    project_id = cl.user_session.get("project_id", GCPConfig.GCP_PROJECT_ID)
    github_repo = cl.user_session.get("github_repo", "")
    
    from tracing import tracer
    with tracer.start_as_current_span(f"chainlit_message_{profile}") as parent_span:
        parent_span.set_attribute("message.content", message.content)
        try:
            # CONFLUENCE ANALYST
            if profile == "analysis_confluence":
                async with cl.Step(name="Docs Assistant") as step:
                    step.output = "Retrieving and analyzing documents..."
                    response, state = await conf_chain(message.content, graph_state)
                    step.output = "Analysis complete."
                
                await cl.Message(content=response).send()
                cl.user_session.set("graph_state", state)
    
            # DATA ANALYST
            elif profile == "analysis_data":
                async with cl.Step(name="SQL Analytics") as step:
                    step.output = "Querying data and generating insights..."
                    state = await data_chain(message.content, graph_state)
                    step.output = "Execution complete."
                    
                query_response = state.generation
                data_response = state.execution
                result = data_response.to_markdown(index=False) if hasattr(data_response, "to_markdown") else str(data_response)
                
                # Format nicely
                response = (
                    f"**Generated SQL Query:**\n```sql\n{query_response}\n```\n\n"
                    f"**Query Result:**\n{result}\n"
                )
                await cl.Message(content=response).send()
                
                chart_type = state.chart_config.get('type')
                if chart_type and chart_type != "table" and hasattr(state, 'plotly') and state.plotly:
                    await cl.Message(content=f"**Generated {chart_type.capitalize()} Chart**", elements=state.plotly).send()
                    
                cl.user_session.set("graph_state", state)
    
            # GCP COST
            elif profile == "gcp_cost":
                msg = cl.Message(content="")
                for chunk in stream_cost_analysis(message.content, project_id=project_id):
                    await msg.stream_token(chunk)
                await msg.update()
    
            # GCP RECOMMENDER
            elif profile == "gcp_recommender":
                msg = cl.Message(content="")
                for chunk in stream_recommendations(message.content, project_id=project_id):
                    await msg.stream_token(chunk)
                await msg.update()
    
            # GITHUB INTEGRATION
            elif profile == "github":
                msg = cl.Message(content="")
                for chunk in stream_github_analysis(message.content, repo=github_repo if github_repo else None):
                    await msg.stream_token(chunk)
                await msg.update()
    
            # CODE OPTIMIZER
            elif profile == "code_optimizer":
                msg = cl.Message(content="")
                for chunk in stream_code_optimization(message.content, project_id=project_id, github_repo=github_repo):
                    await msg.stream_token(chunk)
                await msg.update()
    
            else:
                await cl.Message(
                    content=f"⚠️ No valid agent selected for profile: **{profile}**."
                ).send()
                
        except Exception as e:
            AppLogger.setup().error(f"Error handling message: {e}", exc_info=True)
            parent_span.record_exception(e)
            parent_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            await cl.ErrorMessage(content=f"An error occurred while processing your request: {str(e)}").send()