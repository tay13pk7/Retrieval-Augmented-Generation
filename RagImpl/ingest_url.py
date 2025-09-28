import re
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from db import get_conn

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(text: str) -> str:
    """Clean raw extracted text before chunking."""
    # Remove multiple spaces, tabs, newlines
    text = re.sub(r"\s+", " ", text)
    # Strip leading/trailing junk
    text = text.strip()
    return text

def chunk_text(text, chunk_size=500, overlap=100):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        # clean each chunk to avoid garbage like empty strings
        chunk = clean_text(chunk)
        if chunk:  # only keep non-empty
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def ingest_url(url, doc_name):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠️ Failed to fetch {url}: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    # Get all paragraphs text
    full_text = " ".join([p.get_text(separator=" ") for p in soup.find_all("p")])

    # Clean the extracted text
    full_text = clean_text(full_text)

    if not full_text:
        print(f"⚠️ URL '{url}' returned empty text after cleaning.")
        return

    chunks = chunk_text(full_text)

    conn = get_conn()
    cur = conn.cursor()

    # 🔍 Check if this URL already exists
    cur.execute("SELECT id FROM documents WHERE source = %s;", (url,))
    existing = cur.fetchone()
    if existing:
        print(f"⚠️ Skipping: URL already ingested ({url})")
        cur.close()
        conn.close()
        return

    # Insert document if not already present
    cur.execute(
        "INSERT INTO documents (name, source) VALUES (%s, %s) RETURNING id;",
        (doc_name, url)
    )
    doc_id = cur.fetchone()[0]

    # Insert chunks with embeddings
    for chunk in chunks:
        emb = embed_model.encode(chunk).tolist()
        cur.execute(
            """
            INSERT INTO doc_chunks (document_id, chunk_text, embedding)
            VALUES (%s, %s, %s::vector)
            """,
            (doc_id, chunk, emb)
        )

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Ingested {len(chunks)} clean chunks from URL '{url}'.")

if __name__ == "__main__":
    ingest_url(
        "https://www.digitalocean.com/community/tutorials/multithreading-in-java",
        "Multi-Threading"
    )