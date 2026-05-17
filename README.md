# Insight-Pilot-Agentic-Rag 🚀

Insight Pilot is a highly optimized, fully asynchronous Agentic RAG (Retrieval-Augmented Generation) application built to interact seamlessly with multiple enterprise knowledge sources. It provides an intuitive Chat UI via **Chainlit** and uses **LangGraph** to orchestrate specialized AI agents capable of answering complex analytical questions and searching internal documentation.

## 🌟 Key Features

*   **Multi-Agent Architecture**: Includes specialized agents tailored for distinct tasks:
    *   📘 **Analyst - Confluence**: Searches, retrieves, and summarizes internal knowledge from Confluence workspaces.
    *   📊 **Analyst - Data**: Understands BigQuery dataset schemas via Dataplex, generates complex SQL queries, executes them securely, and automatically plots dynamic charts (Bar, Line, Pie) directly in the chat interface.
*   **High-Performance Async Backend**: Built top-to-bottom with asynchronous Python (`asyncio`, `httpx.AsyncClient`), completely eliminating blocking thread operations during I/O bound tasks.
*   **Token Efficient LLM Grading**: Employs an advanced batch grading system (`with_structured_output`) where the LLM evaluates all retrieved schemas/documents in a single API call, massively reducing LLM token costs and latency.
*   **Intelligent Caching**: In-memory caching automatically intercepts duplicate queries, responding instantly and bypassing redundant external LLM and database calls.
*   **Lazy Loading**: The LLMs and embedding models are implemented using proxy patterns (`LazyLLM`), meaning startup times are instantaneous.
*   **Global VectorDB Pooling**: Uses an optimized class-level `AsyncConnectionPool` for the local `pgvector` database to maintain persistent high-speed connectivity during retrieval.

## 🛠️ Technology Stack

*   **UI Framework**: [Chainlit](https://docs.chainlit.io/) (with custom minimalist CSS)
*   **Agent Orchestration**: [LangGraph](https://python.langchain.com/docs/langgraph) & [LangChain](https://python.langchain.com/)
*   **LLMs & Embeddings**: Google VertexAI (`gemini-2.5-flash`, `text-embedding-004`) / Ollama support.
*   **Databases**: PostgreSQL with `pgvector` (via `psycopg_pool`)
*   **Enterprise Integrations**: Google BigQuery, Google Dataplex, Confluence API

## 📋 Prerequisites

*   Python 3.10+
*   Docker & Docker Compose (for running the local `pgvector` database)
*   Google Cloud Platform (GCP) credentials with access to VertexAI, BigQuery, and Dataplex.
*   Confluence API Token (for the Confluence Analyst)

## 🚀 Getting Started

### 1. Environment Setup

Clone the repository and set up a `.env` file in the root directory:

```env
# Confluence Credentials
CONFLUENCE_API_KEY=your_confluence_api_key

# PostgreSQL VectorDB
PGVECTOR_CONNECTION_STRING=postgresql://user:password@localhost:5432/vectordb

# GCP (Ensure your service account is authenticated locally using gcloud auth application-default login)
GOOGLE_CLOUD_PROJECT=insight-pilot-trios
```

### 2. Start the Vector Database

Insight Pilot uses a local Docker container for its vector database. Ensure docker is running, then spin up the DB:

```bash
# Example if using docker directly
docker run --name pgvector-db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=vectordb -p 5432:5432 -d pgvector/pgvector:pg16
```

### 3. Run the Ingestion Pipeline

Before chatting, ingest your enterprise data into the vector database:

```bash
python src/ingest.py
```
*(This will fetch updated Confluence pages, Dataplex schemas, and store their embeddings natively using the `AsyncConnectionPool`)*

### 4. Launch the Application

Start the Chainlit user interface:

```bash
chainlit run src/app.py -w
```

The application will be accessible at `http://localhost:8000`. Select your desired agent profile from the chat interface and start exploring your data!

## 🤝 Contributing

This project is currently a prototype. All contributions, issues, and feature requests are welcome!