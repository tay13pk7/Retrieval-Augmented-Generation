import os
import re
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from .db import get_conn
from RagImpl.db import get_conn

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(text: str) -> str:
    """Clean raw text extracted from PDF before chunking."""
    text = re.sub(r"\s+", " ", text)  # collapse whitespace/newlines/tabs
    return text.strip()

def chunk_text(text, chunk_size=500, overlap=100):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunk = clean_text(chunk)
        if chunk:  # only keep non-empty chunks
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def ingest_pdf(path, doc_name, debug=True):
    """Ingest a single PDF into the database with cleaning."""
    if not os.path.exists(path):
        print(f"⚠️ PDF file not found: {path}")
        return

    # check if this PDF is already ingested
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM documents WHERE name = %s AND source = %s", (doc_name, "pdf"))
    if cur.fetchone():
        print(f"ℹ️ PDF '{doc_name}' already ingested, skipping.")
        cur.close()
        conn.close()
        return

    reader = PdfReader(path)
    full_text = "\n".join([p.extract_text() or "" for p in reader.pages])
    full_text = clean_text(full_text)

    if not full_text:
        print(f"⚠️ PDF '{doc_name}' is empty after cleaning, skipping.")
        cur.close()
        conn.close()
        return

    chunks = chunk_text(full_text)

    if debug:
        print(f"📄 PDF '{doc_name}' produced {len(chunks)} chunks.")
        for idx, ch in enumerate(chunks[:5]):  # show first 5 chunks only
            preview = " ".join(ch.split()[:12])  # first 12 words
            print(f"   🔹 Chunk {idx+1}: {preview}...")

    cur.execute("INSERT INTO documents (name, source) VALUES (%s, %s) RETURNING id;",
                (doc_name, "pdf"))
    doc_id = cur.fetchone()[0]

    for chunk in chunks:
        emb = embed_model.encode(chunk).tolist()
        cur.execute("""
            INSERT INTO doc_chunks (document_id, chunk_text, embedding)
            VALUES (%s, %s, %s::vector)
        """, (doc_id, chunk, emb))

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ PDF '{doc_name}' ingested successfully with {len(chunks)} chunks.")

def ingest_pdfs(pdf_files, debug=True):
    """Ingest multiple PDFs safely."""
    if not pdf_files:
        print("ℹ️ No PDF files provided, skipping ingestion.")
        return

    for pdf_path in pdf_files:
        doc_name = os.path.basename(pdf_path)
        ingest_pdf(pdf_path, doc_name, debug=debug)

if __name__ == "__main__":
    # Example usage with multiple files
    pdf_list = [
        r"D:\ProjectX\projectPDF\IEEE Paper.pdf",
        # r"D:\ProjectX\projectPDF\sample2.pdf"  # add more if needed
    ]
    ingest_pdfs(pdf_list, debug=True)