# AskData - AI Data Analyst Agent

> Live demo: **<add your link here>**

Ask questions in plain English. The agent decides whether to answer from a **SQL database** (text-to-SQL), from **documents** (RAG with citations), or **both**, then returns a grounded answer, the SQL used, sources, and an auto-generated chart.

<!-- add demo.gif here -->

## Features
- Router agent (LangGraph): SQL / DOCS / BOTH / CHAT, with follow-up question condensation
- Text-to-SQL with live schema, glossary, sample rows and a 3-try self-correction loop
- SQL guardrails: AST validation (sqlglot), read-only connection, row limit, timeout
- Document RAG (ChromaDB + bge-small embeddings, optional reranker) with file/page citations
- Auto charts from a JSON spec rendered by Plotly (no LLM-written code is ever executed)
- Streamlit chat UI, CSV download, Markdown report export, JSONL logging, caching
- Evaluation harness: execution accuracy, router accuracy, hit-rate@k

## Architecture
condense -> route -> [SQL -> chart] -> [RAG] -> synthesize (answer + citations)

## Evaluation results (replace with YOUR measured numbers)
| Version | Change | Execution accuracy |
|---|---|---|
| v0 | Baseline: schema only | _ % |
| v1 | + sample rows and glossary | _ % |
| v2 | + few-shot examples | _ % |
| v3 | + self-correction loop | _ % |

Router accuracy: _ % (N questions) | Retrieval hit-rate@5: _ % (N questions)

## Safety
Three layers: AST validation, read-only DB connection, timeout + row limit. Retrieved text is treated as data (prompt-injection test document included).

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # add your LLM key
# download Olist CSVs from Kaggle into data/raw/
python -m scripts.load_data
python -m scripts.ingest_docs
streamlit run app.py
```

## Limitations
Documents are synthetic; data is the public Olist dataset. SQLite only; no authentication.
