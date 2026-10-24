"""Chunk + embed everything in data/docs.  Run: python -m scripts.ingest_docs"""
from src.rag.store import ingest

if __name__ == "__main__":
    print(f"Ingested {ingest()} chunks")
