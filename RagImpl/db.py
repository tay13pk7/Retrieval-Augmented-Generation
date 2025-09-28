import psycopg2

PG_CONN = "postgresql://postgres:prasad@localhost:5433/postgres"
EMBED_DIM = 384  # all-MiniLM-L6-v2

def get_conn():
    return psycopg2.connect(PG_CONN)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            source TEXT,
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS doc_chunks (
            id SERIAL PRIMARY KEY,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            chunk_text TEXT NOT NULL,
            embedding vector({EMBED_DIM}),
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized.")

if __name__ == "__main__":
    init_db()