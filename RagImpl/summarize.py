# summarize.py
from RagImpl.utils import get_conn
from RagImpl.ollama_client import ask_ollama
from RagImpl.db import get_conn

DEBUG = True


def get_document_chunks(doc_id: int):
    """Fetch all chunks for a given document ID from the database."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT dc.chunk_text
        FROM doc_chunks dc
        WHERE dc.document_id = %s
        ORDER BY dc.id
    """, (doc_id,))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [r[0] for r in rows]


def summarize_document(doc_id: int, doc_name: str) -> str:
    """Summarize the full content of a document (URL or PDF)."""
    chunks = get_document_chunks(doc_id)

    if not chunks:
        return f"⚠️ No content found for document '{doc_name}'."

    # Concatenate all chunks (can be long, so keep prompt strict)
    context = "\n\n---\n\n".join(chunks)

    prompt = f"""
You are a precise summarizer.
Your task is to summarize the following document into a few clear lines.

Rules:
- Use ONLY the provided document text.
- Do NOT add any information that is not present in the document.
- Keep the summary concise (3–5 sentences).
- If the document is empty, reply with: "No content available to summarize."

Document Name: {doc_name}

DOCUMENT CONTENT:
{context}

Summary:
"""

    response = ask_ollama(prompt)
    return response


if __name__ == "__main__":
    # Example usage: summarize document with ID 1
    doc_id = 11
    doc_name = "https://www.digitalocean.com/community/tutorials/multithreading-in-java"  # or any name you gave during ingestion
    summary = summarize_document(doc_id, doc_name)
    print("\n>>> SUMMARY:\n", summary, "\n")