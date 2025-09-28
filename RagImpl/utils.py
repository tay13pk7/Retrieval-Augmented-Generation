import psycopg2
from sentence_transformers import SentenceTransformer

# Load embedding model once
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# ---------------- Embeddings ----------------
def get_embedding(text):
    """Convert text to embedding (list of floats)."""
    return embed_model.encode(text).tolist()

def vector_to_pgvector(arr):
    """Convert Python list of floats into Postgres vector literal."""
    return "[" + ",".join(map(str, arr)) + "]"

# ---------------- DB Connection ----------------
PG_CONN = "postgresql://postgres:prasad@localhost:5433/postgres"

def get_conn():
    """Get a fresh PostgreSQL connection."""
    return psycopg2.connect(PG_CONN)