from utils import get_embedding, vector_to_pgvector, get_conn
from ollama_client import ask_ollama



TOP_K = 5
SIMILARITY_THRESHOLD = 0.3  # tune if needed
DEBUG = True                 # set False to silence debug printouts

def _print_debug(rows):
    print("\n--- Retriever debug (top candidates) ---")
    for i, r in enumerate(rows, start=1):
        doc_name = r.get("doc_name", "unknown")
        print(f"{i}. doc_id={r['doc_id']} doc='{doc_name}' distance={r['distance']:.4f} similarity={r['similarity']:.3f}")
        excerpt = r['chunk_text'][:350].replace("\n", " ")
        print("   excerpt:", excerpt, "\n")
    print("--- end debug ---\n")

def search_chunks(query, top_k = TOP_K):
    """
    Retrieval strategy:
      1) Exact phrase search (ILIKE) for multi-word queries.
      2) Vector similarity fallback (<->).
      3) Returns list of dicts with distance & similarity.
    """
    q_emb = get_embedding(query)
    q_emb_pg = vector_to_pgvector(q_emb)

    conn = get_conn()
    cur = conn.cursor()

    # 1) Exact phrase search (heading/substring match)
    phrase_found_rows = []
    phrase = query.strip()
    if len(phrase.split()) >= 2:
        cur.execute("""
            SELECT dc.id, dc.chunk_text, dc.document_id, d.name
            FROM doc_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE dc.chunk_text ILIKE %s
            LIMIT %s
        """, (f"%{phrase}%", top_k))
        fetched = cur.fetchall()
        for row in fetched:
            phrase_found_rows.append({
                "chunk_text": row[1],
                "doc_id": row[2],
                "doc_name": row[3],
                "distance": 0.0,
                "similarity": 1.0
            })

    if phrase_found_rows:
        if DEBUG:
            _print_debug(phrase_found_rows)
        cur.close(); conn.close()
        return phrase_found_rows

    # 2) Vector similarity fallback (cosine distance <=>)
    cur.execute("""
        SELECT dc.id, dc.chunk_text, dc.document_id, d.name, (dc.embedding <=> %s::vector) AS distance
        FROM doc_chunks dc
        JOIN documents d ON d.id = dc.document_id
        ORDER BY dc.embedding <=> %s::vector
        LIMIT %s
    """, (q_emb_pg, q_emb_pg, top_k))

    # # 2) Vector similarity fallback, this was similarity search
    # cur.execute("""
    #     SELECT dc.id, dc.chunk_text, dc.document_id, d.name, (dc.embedding <-> %s::vector) AS distance
    #     FROM doc_chunks dc
    #     JOIN documents d ON d.id = dc.document_id
    #     ORDER BY dc.embedding <-> %s::vector
    #     LIMIT %s
    # """, (q_emb_pg, q_emb_pg, top_k))

    rows = cur.fetchall()
    results = []
    for row in rows:
        distance = row[4]
        similarity = 1.0 / (1.0 + distance)  # bounded similarity
        results.append({
            "chunk_text": row[1],
            "doc_id": row[2],
            "doc_name": row[3],
            "distance": distance,
            "similarity": similarity
        })

    cur.close(); conn.close()

    if DEBUG:
        _print_debug(results)

    return results

def ask(query: str) -> str:
    """Main RAG function with strict prompt + multiple chunks support."""
    candidates = search_chunks(query, top_k=TOP_K)
    if not candidates:
        return "I don’t know. The ingested documents don’t contain this information."

    # keep all chunks above threshold
    valid_chunks = [c for c in candidates if c["similarity"] >= SIMILARITY_THRESHOLD]

    if not valid_chunks:
        if DEBUG:
            print("No chunks passed the similarity threshold.")
        return "I don’t know. The ingested documents don’t contain this information."

    # Concatenate multiple chunks as context
    context = "\n\n---\n\n".join(c["chunk_text"] for c in valid_chunks)

    # Strict anti-hallucination prompt
    prompt = f"""
You are a strict assistant. Use ONLY the provided CHUNKS to answer the question.
- If the answer is in the CHUNKS, extract only that part.
- Do NOT add any extra information beyond what is in the CHUNKS.
- If the CHUNKS do not contain the answer, reply exactly:
"I don’t know. The ingested documents don’t contain this information."

Question:
{query}

CHUNKS:
{context}

Answer:
"""

    response = ask_ollama(prompt)
    return response

if __name__ == "__main__":
    print("RAG system ready. Ask your question (type exit to quit).")
    while True:
        q = input("Ask: ").strip()
        if q.lower() in ("exit", "quit"):
            break
        if not q:
            continue
        out = ask(q)
        print("\n>>> ANSWER:\n", out, "\n")