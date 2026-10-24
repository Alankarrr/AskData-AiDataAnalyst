"""Central configuration: paths, model names, thresholds."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
_full_db, _sample_db = ROOT / "data" / "olist.db", ROOT / "data" / "olist_sample.db"
# Use the full DB locally; fall back to the sampled DB on deployments where only it is committed.
DB_PATH = os.getenv("DB_PATH") or str(_full_db if _full_db.exists() or not _sample_db.exists() else _sample_db)
DOCS_DIR = ROOT / "data" / "docs"
GLOSSARY_PATH = ROOT / "data" / "glossary.md"
PROMPTS_DIR = ROOT / "prompts"
VECTOR_DIR = ROOT / "vectorstore"
LOG_PATH = ROOT / "logs" / "events.jsonl"

LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or None
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
USE_RERANKER = os.getenv("USE_RERANKER", "0") == "1"

TOP_K = 5
CHUNK_SIZE = 900
CHUNK_OVERLAP = 120

MAX_ROWS = 1000
SQL_TIMEOUT_S = 15
MAX_RETRIES = 3

MAX_QUESTIONS_PER_SESSION = int(os.getenv("MAX_QUESTIONS_PER_SESSION", "30"))


def read_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")
