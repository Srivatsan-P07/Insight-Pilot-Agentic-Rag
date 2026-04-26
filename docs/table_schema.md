
### Recommended Schema

```sql
CREATE TABLE document_embeddings (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,         -- e.g., 'github', 'web_url', 'jira'
    external_id TEXT NOT NULL,         -- page_url or ticket_id
    content TEXT NOT NULL,             -- Original text for retrieval and LLM processing
    embedding vector(768),             -- Adjust 768 based on your embedding model
    metadata JSONB,                    -- Store flexible source-specific attributes
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### Key Schema Improvements

1.  **Content Column (Essential)**: 
    Vector similarity searches return IDs or URLs, but you need the actual text to send to Ollama for response generation. Storing the text chunk alongside the embedding eliminates the need for external lookups.

2.  **JSONB Metadata Field**: 
    Instead of creating columns for every source attribute, use JSONB to flexibly store `author`, `line_number`, `repo_stars`, and other varied metadata without schema modifications.

3.  **Appropriate Vector Dimensions**:
    Match your embedding model size:
    * **nomic-embed-text** (Ollama): `vector(768)`
    * **mxbai-embed-large** (Ollama): `vector(1024)`

---

### Indexing for Performance

Add an HNSW index for efficient similarity searches on large datasets:

```sql
CREATE INDEX ON document_embeddings 
USING hnsw (embedding vector_cosine_ops);
```

HNSW provides fast and accurate vector search performance at scale.

