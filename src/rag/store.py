"""ChromaDB ingest + retrieve (+ optional cross-encoder rerank). Models load lazily."""
from pathlib import Path

import chromadb
from sentence_transformers import CrossEncoder, SentenceTransformer

from src import config
from src.rag.chunking import chunk_text
from src.rag.loaders import load_pages

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
_embedder = None
_reranker = None
_client = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(config.EMBED_MODEL)
    return _embedder


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(config.VECTOR_DIR))
    return _client


def _get_collection(reset: bool = False):
    client = _get_client()
    if reset:
        try:
            client.delete_collection("docs")
        except Exception:
            pass
    return client.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})


def ingest(doc_dir: Path = config.DOCS_DIR) -> int:
    """Rebuild the vector store from every PDF/MD/TXT file. Returns number of chunks."""
    col = _get_collection(reset=True)
    ids, docs, metas = [], [], []
    for path in sorted(Path(doc_dir).glob("*")):
        for page_no, text in load_pages(path):
            for i, chunk in enumerate(chunk_text(text)):
                ids.append(f"{path.name}-{page_no}-{i}")
                docs.append(chunk)
                metas.append({"source": path.name, "page": page_no})
    if not docs:
        raise RuntimeError(f"No documents found in {doc_dir}")
    emb = _get_embedder().encode(docs, normalize_embeddings=True).tolist()
    col.add(ids=ids, documents=docs, metadatas=metas, embeddings=emb)
    return len(docs)


def retrieve(question: str, k: int = config.TOP_K, rerank: bool | None = None) -> list[dict]:
    global _reranker
    rerank = config.USE_RERANKER if rerank is None else rerank
    col = _get_collection()
    if col.count() == 0:  # e.g. fresh deployment: build the store on first use
        ingest()
        col = _get_collection()
    n = max(k, 15) if rerank else k
    q = _get_embedder().encode([QUERY_PREFIX + question], normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=q, n_results=min(n, col.count()))
    hits = [{"text": d, "source": m["source"], "page": m["page"], "distance": dist}
            for d, m, dist in zip(res["documents"][0], res["metadatas"][0],
                                  res["distances"][0])]
    if rerank:
        if _reranker is None:
            _reranker = CrossEncoder(config.RERANK_MODEL)
        scores = _reranker.predict([(question, h["text"]) for h in hits])
        hits = [h for _, h in sorted(zip(scores, hits), key=lambda x: -x[0])]
    return hits[:k]
