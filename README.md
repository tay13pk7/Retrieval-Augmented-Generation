Chat with Docs — RAG System

A production-grade Retrieval-Augmented Generation (RAG) platform that enables intelligent interaction with PDFs and web content using semantic search, embeddings, and LLM-powered summarization — all exposed via a robust FastAPI backend.

---------------------------------------------------------------------

What This Project Does

This system allows users to:

📂 Upload PDF documents

🌐 Ingest web articles / URLs

🔍 Ask natural language questions over their data

🧾 Generate concise, hallucination-free summaries

⚡ Interact through a clean REST API

It combines modern NLP, vector databases, and LLMs into a scalable document-intelligence platform.

---------------------------------------------------------------------------

## 🧩 Tech Stack

| Layer         | Technology                                      |
|--------------|------------------------------------------------|
| Backend      | FastAPI                                         |
| Vector Store | PostgreSQL + pgvector                           |
| Embeddings   | SentenceTransformers (all-MiniLM-L6-v2)         |
| LLM          | Ollama (Mistral)                                |
| Parsing      | PyPDF, BeautifulSoup                            |


-------------------------------------------------------------------------------

✨ Key Features

* Hallucination-resistant answers using strict context injection

* Semantic document search with cosine similarity

* Multi-document summarization

* Clean text pipeline (whitespace & noise removal)

* Duplicate ingestion protection

* FastAPI interactive docs

------------------------------------------------------------------------------



- Example Use Case

1.Upload annual report PDFs
2.Ingest industry articles from the web
3.Ask: “Summarize the company’s AI strategy”
4.Receive concise, context-grounded answers in seconds
