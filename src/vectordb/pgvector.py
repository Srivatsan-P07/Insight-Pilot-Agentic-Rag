from psycopg_pool import AsyncConnectionPool
from pgvector.psycopg import register_vector_async
from psycopg import sql
import json


async def _configure_conn(conn):
    await register_vector_async(conn)


class PGVectorDB:
    def __init__(self, connection_string: str, source_type: str):
        self.connection_string = connection_string
        self.source_type = source_type
        self.pool = AsyncConnectionPool(
            conninfo=self.connection_string,
            min_size=1,
            max_size=10,
            open=False,
            configure=_configure_conn
            )
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
        await self.pool.open()
        self._pool_opened = True
        async with self.pool.connection() as conn:
            await self._create_table(conn)
       

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
                CREATE INDEX IF NOT EXISTS idx_embedding_hnsw
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
        table_name = sql.Identifier(f"{self.source_type}_document_embeddings")

        async with self.pool.connection() as conn:
            await register_vector_async(conn)  # ✅ do this once per connection

            data = []
            for d in pages:
                emb = self.normalize_embedding(d['embedding'])
                if emb is None:
                    continue

                data.append((
                    d['source_type'],
                    d['external_id'],
                    emb,  # ✅ pass list directly
                    json.dumps(d['metadata']) if 'metadata' in d else None
                ))

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

    async def close(self):
        if hasattr(self, '_pool_opened') and self._pool_opened:
            await self.pool.close()