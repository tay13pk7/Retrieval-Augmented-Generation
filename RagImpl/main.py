# main.py

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse

from .ingest_pdf import ingest_pdfs
from .ingest_url import ingest_url
from .query import ask
from .summarize import summarize_document
from .db import get_conn

import os

app = FastAPI(title="RAG API", description="RAG system with PDF/URL ingestion, querying, and summarization.")


@app.post("/upload/pdf")
async def upload_pdf(files: list[UploadFile]):
    """Upload and ingest one or more PDFs."""
    saved_paths = []

    for file in files:
        contents = await file.read()
        save_path = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(contents)
        saved_paths.append(save_path)

    # ingest PDFs
    ingest_pdfs(saved_paths)
    return {"message": f"✅ Uploaded and ingested {len(saved_paths)} PDF(s)."}


@app.post("/upload/url")
async def upload_url(url: str = Form(...), doc_name: str = Form(...)):
    """Ingest a single URL."""
    ingest_url(url, doc_name)
    return {"message": f"✅ URL '{url}' ingested successfully."}


@app.post("/query")
async def query_doc(query: str = Form(...)):
    """Ask a question from the RAG system."""
    answer = ask(query)
    return {"query": query, "answer": answer}


@app.get("/summarize/{doc_id}")
async def summarize_doc(doc_id: int):
    """Summarize a single document by ID."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM documents WHERE id = %s;", (doc_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return JSONResponse(status_code=404, content={"error": f"Document with ID {doc_id} not found."})

    doc_name = row[0]
    summary = summarize_document(doc_id, doc_name)
    return {"doc_id": doc_id, "doc_name": doc_name, "summary": summary}


@app.get("/")
async def home():
    return {"message": "🚀 RAG API is running! Use /docs to explore the endpoints."}