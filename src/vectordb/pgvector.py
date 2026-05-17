from psycopg_pool import AsyncConnectionPool
from pgvector.psycopg import register_vector_async
from psycopg import sql
import json
from config import Config, GCPConfig
from pgvector.psycopg import register_vector
import logging


logger = logging.getLogger(__name__)

async def _configure_conn(conn):
    await register_vector_async(conn)


class PGVectorDB:
    _pools = {}

    def __init__(self, connection_string: str, source_type: str):
        self.connection_string = connection_string
        self.source_type = source_type
        
        if self.connection_string not in PGVectorDB._pools:
            PGVectorDB._pools[self.connection_string] = AsyncConnectionPool(
                conninfo=self.connection_string,
                min_size=1,
                max_size=10,
                open=False,
                configure=_configure_conn
            )
        self.pool = PGVectorDB._pools[self.connection_string]
        self.table_name = sql.Identifier(f"{source_type}_document_embeddings")

    async def _get_conn(self):
        conn = await self.pool.getconn()
        try:
            await register_vector_async(conn)  # ✅ async-safe here
            return conn
        except Exception:
            await self.pool.putconn(conn)
            raise

    async def connect(self):
        logger.info(f"Connecting to PGVector database for source: {self.source_type}")
        try:
            await self.pool.open()
        except Exception:
            pass # Pool might already be open
        
        async with self.pool.connection() as conn:
            await self._create_table(conn)
        logger.info("Database connection and table initialization complete.")
       

    async def _create_table(self, conn):
        table_name = sql.Identifier(f"{self.source_type}_document_embeddings")

        query = sql.SQL("""
            CREATE EXTENSION IF NOT EXISTS vector;
            CREATE EXTENSION IF NOT EXISTS pgcrypto;

            CREATE TABLE IF NOT EXISTS {} (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source_type TEXT NOT NULL,
                external_id TEXT NOT NULL UNIQUE,
                embedding vector(768),
                metadata JSONB,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """).format(table_name)

        async with conn.cursor() as cur:
            await cur.execute(query)

        # create index separately (cleaner)
        async with conn.cursor() as cur:
            await cur.execute(sql.SQL("""
                CREATE INDEX IF NOT EXISTS idx_embedding_vector
                ON {} USING hnsw (embedding vector_cosine_ops);
            """).format(table_name))

    @staticmethod
    def normalize_embedding(e):
        if e is None:
            return None

        if hasattr(e, "tolist"):
            e = e.tolist()

        # flatten [[...]] → [...]
        if isinstance(e, list) and len(e) == 1 and isinstance(e[0], list):
            e = e[0]

        if not e:
            return None

        return e  # ✅ keep as list


    async def store_embeddings(self, pages):
        logger.info(f"Storing {len(pages)} embeddings into {self.source_type}_document_embeddings")
        table_name = sql.Identifier(f"{self.source_type}_document_embeddings")

        async with self.pool.connection() as conn:
            await register_vector_async(conn)  # ✅ do this once per connection

            def prepare_row(d):
                if d is None:
                    return None
                emb = self.normalize_embedding(d['embedding'])
                if emb is None:
                    return None
                return (
                    d['source_type'],
                    d['external_id'],
                    emb,
                    json.dumps(d['metadata']) if 'metadata' in d else None
                )

            data = [prepare_row(p) for p in pages]
            data = [row for row in data if row is not None]

            async with conn.transaction():
                async with conn.cursor() as cur:
                    await cur.executemany(
                        sql.SQL("""
                            INSERT INTO {}
                            (source_type, external_id, embedding, metadata)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (external_id) DO UPDATE SET
                                embedding = EXCLUDED.embedding,
                                metadata = EXCLUDED.metadata
                        """).format(table_name),
                        data
                    )
            logger.info("Successfully stored embeddings.")

    async def query_similar(self, text, top_k=5):
        logger.info(f"Querying similar documents for text: {text[:50]}...")
        table_name = sql.Identifier(f"{self.source_type}_document_embeddings")

        embedder = GCPConfig.get_embedding_model()
        embedding = await embedder.aembed_query(text)
        embedding = self.normalize_embedding(embedding)
        logger.info("Text embedded and normalized for query.")

        async with self.pool.connection() as conn:
            await register_vector_async(conn)  # ✅ do this once per connection

            async with conn.cursor() as cur:
                await cur.execute(
                    sql.SQL("""
                        SELECT external_id, source_type, metadata, embedding <-> %s::vector AS distance
                        FROM {}
                        ORDER BY embedding <-> %s::vector
                        LIMIT %s
                    """).format(table_name),
                    (embedding, embedding, top_k)
                )
                results = await cur.fetchall()

        logger.info(f"Found {len(results)} similar documents.")

        def format_result(r):
            return {
                "external_id": r[0],
                "source_type": r[1],
                "metadata": r[2],
                "distance": r[3],
            }

        return [format_result(r) for r in results]
    
    async def close(self):
        if hasattr(self, '_pool_opened') and self._pool_opened:
            logger.info("Closing PGVector database connection pool.")
            await self.pool.close()