# AskData — AI Data Analyst Agent

An agentic analytics assistant: ask a question in plain English and the agent
decides whether the answer lives in a **SQL database** (text-to-SQL), in
**business documents** (RAG with citations), or **both**. It returns a grounded
answer, the SQL it ran, the document passages it used, and an auto-generated
chart when a chart helps.

**Live demo: [askdataanalyst.streamlit.app](https://askdataanalyst.streamlit.app/)**

<p>
  <a href="https://askdataanalyst.streamlit.app/"><img alt="demo" src="https://img.shields.io/badge/live%20demo-Streamlit-FF4B4B"></a>
  <img alt="python" src="https://img.shields.io/badge/backend-Python%203.12-3776AB">
  <img alt="agent" src="https://img.shields.io/badge/agent-LangGraph-1C3C3C">
  <img alt="sql" src="https://img.shields.io/badge/SQL%20accuracy-96.9%25-2EA043">
  <img alt="tests" src="https://img.shields.io/badge/tests-25%20passing-0A9EDC">
</p>

<!-- Add a short demo GIF here: ![demo](docs/demo.gif) -->

> **Note on the live demo:** it runs on a ~10% sample of the database so it can
> be hosted for free, so its numbers differ from the full-dataset results below.
> The business documents are **synthetic** (see [Limitations](#limitations)).

## What it does

- **Routes every question** to one of four paths: `SQL`, `DOCS`, `BOTH` or `CHAT`.
- **Text-to-SQL** over the Olist e-commerce database, using the live schema,
  sample rows, a business glossary with join paths, and few-shot examples.
- **Self-correcting SQL loop:** if a query fails, the error goes back to the
  LLM for up to 3 repair attempts.
- **SQL guardrails:** single `SELECT` only, checked on the parsed AST, run on a
  read-only connection with an automatic `LIMIT` and an execution timeout.
- **Document RAG with citations:** PDF/Markdown/TXT are chunked, embedded and
  stored in ChromaDB; answers cite the source file and page, and say so when
  the documents don't contain the answer.
- **Follow-up questions:** "and for 2018?" is rewritten into a standalone
  question using the recent chat history before routing.
- **Auto charts:** the LLM proposes a small JSON chart spec and the app renders
  it with Plotly. No LLM-written code is ever executed.
- **Chat UI** with expandable panels for *SQL used*, *Raw data* and *Sources*,
  CSV download, Markdown report export, a usage-stats panel, response caching
  and a per-session question limit.

### Example questions

| Question | Route | What the agent does |
|---|---|---|
| Top 5 product categories by revenue in 2017 | SQL | Writes a multi-table JOIN + GROUP BY, runs it read-only, shows table and chart |
| What is the refund policy for late deliveries? | DOCS | Retrieves policy chunks and answers only from them, with citations |
| Why did delivery delays rise in November 2017, and what does the ops report say? | BOTH | Pulls numbers with SQL, retrieves the incident report, merges both |
| Plot monthly orders for the top 3 states | SQL + chart | Writes the query, then draws a multi-series Plotly line chart |
| and for 2018? | Follow-up | Condenses history into a standalone question, then routes it |

## Evaluation results

The agent is benchmarked, not just demoed. Evaluation runs against the **full**
Olist database (~100k orders) with `openai/gpt-oss-120b` served through Groq,
temperature 0.

### Text-to-SQL (32 questions: 13 easy, 14 medium, 5 hard)

Scored by **execution accuracy**: the result set of the generated SQL must
match the result set of hand-written gold SQL (the SQL text itself can differ).

| Run | Setup | Execution accuracy | Valid-SQL rate | Avg. retries |
|---|---|---|---|---|
| v0 | Schema + sample rows + glossary + few-shot (two examples overlapped benchmark questions) + self-correction loop | 93.8% (30/32) | 100% | 0.0 |
| v1 | Same pipeline, few-shot examples replaced with non-overlapping ones, SQL timeout 5 s → 15 s | **96.9% (31/32)** | 100% | 0.0 |

The one remaining failure in v1 is q022 (*"Who are the top 5 sellers by
revenue?"*). Per-question details, including the generated SQL, are in
[`eval/results/`](eval/results/). The v0 → v1 difference is a single question,
which is within normal run-to-run variation, so treat the two runs as
"about 94–97%", not as a proven improvement.

### Router and retrieval

| Component | Metric | Result | Benchmark size |
|---|---|---|---|
| Router | Routing accuracy (SQL / DOCS / BOTH / CHAT) | 100% | 7 questions |
| Retrieval | Hit-rate@5 (expected source in top 5 chunks) | 100% | 26 questions |

These two benchmarks are small, and the retrieval one is easy: the document
set is only 7 short files (7 chunks), so a top-5 search nearly always contains
the right file. Expanding the document set and the question sets is the first
item under [Future work](#future-work).

### Safety

- **25 automated tests** pass (`pytest`): 11 attack strings (DROP, DELETE,
  UPDATE, INSERT, CREATE, PRAGMA, ATTACH, multi-statement and hidden-comment
  injections, odd casing) are all rejected, `LIMIT` is added, read-only mode
  and timeout are enforced, and chunking and router parsing are covered.
- A **prompt-injection test document** (`adversarial_note.md`, containing
  "ignore previous instructions") sits in the document set. Retrieved text is
  wrapped in `<document>` tags and the synthesis prompt treats it as data, never
  as instructions.

### Reproduce the numbers

```bash
python -m eval.run_eval sql    --tag v1
python -m eval.run_eval router --tag v1
python -m eval.run_eval rag    --tag v1
```

Results are saved as JSON in `eval/results/`.

## Architecture

```
User question (Streamlit chat)
        │
        ▼
┌───────────────────┐
│ Condense follow-up│  (skipped when there is no history)
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  Router (LLM)     │  SQL | DOCS | BOTH | CHAT
└───┬─────┬─────┬───┘
    │     │     └──────────────┐
    ▼     ▼                    ▼
 SQL path   RAG path        CHAT reply
 schema +   embed question
 glossary   → ChromaDB top-k
 → LLM SQL  (+ optional rerank)
 → validate
 → read-only run
 → self-correct
    │
    ▼
 Chart node (JSON spec → Plotly)
    │
    └────────► Synthesizer: answer + citations + SQL + chart
                      │
                      ▼
              JSONL log (route, SQL, retries, latency)
```

For `BOTH` questions the graph runs SQL, then chart, then RAG, then the
synthesizer. All nodes read from and write to one typed state object
(`question`, `history`, `route`, `sql`, `table`, `passages`, `figure`, `answer`).

## Project structure

```
ai-data-analyst/
├── app.py                  # Streamlit UI
├── data/
│   ├── glossary.md         # metric definitions + join paths
│   ├── docs/               # business documents for RAG (synthetic)
│   └── olist_sample.db     # ~10% sample used by the hosted demo
├── prompts/                # SQL, router, synthesis, chart, few-shot prompts
├── src/
│   ├── config.py
│   ├── llm/                # provider-agnostic OpenAI-compatible client
│   ├── sql/                # schema.py, generator.py, guardrails.py
│   ├── rag/                # loaders.py, chunking.py, store.py
│   ├── agent/              # router, memory, synthesizer, LangGraph graph
│   ├── viz/charts.py       # JSON spec → Plotly
│   └── utils/              # logging, cache
├── eval/                   # golden sets, run_eval.py, results/
├── scripts/                # load_data, make_sample_db, ingest_docs, cli
└── tests/                  # guardrail, chunking, router tests
```

## Getting started

Requires **Python 3.12** (3.14 is too new for some dependencies) and a free
LLM API key from any OpenAI-compatible provider (for example Groq).

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`):

```
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your_key_here
LLM_MODEL=openai/gpt-oss-120b
```

Download the **Olist Brazilian E-Commerce** CSV files from
[Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) into
`data/raw/`, then:

```bash
python -m scripts.load_data       # build data/olist.db
python -m scripts.ingest_docs     # embed documents into ChromaDB
streamlit run app.py
```

Without the full database the app falls back to `data/olist_sample.db`.
Model names change often, so check your provider's documentation if you get a
"model not found" error.

### Other commands

```bash
python -m scripts.cli             # chat in the terminal
pytest                            # run the 25 tests
python -m scripts.make_sample_db  # rebuild the small demo database
```

## Deploying on Streamlit Community Cloud

1. Push the repository to GitHub (the full `olist.db`, `.env` and raw CSVs are
   git-ignored; the small sample database is committed).
2. On [share.streamlit.io](https://share.streamlit.io), create an app from the
   repo with main file `app.py`.
3. Add your key under **Advanced settings → Secrets**:
   ```
   LLM_BASE_URL = "https://api.groq.com/openai/v1"
   LLM_API_KEY = "your_key"
   LLM_MODEL = "openai/gpt-oss-120b"
   MAX_QUESTIONS_PER_SESSION = "15"
   ```

The vector store is built automatically on the first document question.

## Design notes

- **Defence in depth for SQL.** Three independent layers: AST validation (what
  a query is allowed to be), a read-only SQLite connection (what the connection
  may do), and a row limit plus timeout (how much damage a heavy query can do).
- **JSON specs instead of generated code.** Charts are drawn from a small JSON
  spec the app validates against the real result columns, which is safer and
  far more reliable than executing LLM-written Python.
- **Execution accuracy, not string matching.** Two different SQL queries can be
  equally correct, so the benchmark compares result sets.
- **Grounded answers.** The synthesis prompt allows only the supplied evidence,
  requires citations, and tells the model to say what is missing instead of
  guessing; document text is treated as data, never as instructions.
- **Provider-agnostic LLM layer.** One wrapper serves any OpenAI-compatible
  endpoint (Groq, Gemini, Ollama, OpenAI) with retries and backoff.

## Tech stack

**Language:** Python 3.12
**Agent:** LangGraph
**LLM:** OpenAI-compatible API (`openai/gpt-oss-120b` via Groq)
**SQL:** SQLite, pandas, sqlglot
**RAG:** ChromaDB, sentence-transformers (`BAAI/bge-small-en-v1.5`)
**Visualisation and UI:** Plotly, Streamlit
**Quality:** pytest, ruff

## Limitations

- The business documents (refund policy, delivery SLA, KPI definitions,
  incident and quarterly reports, FAQ) are **synthetic**, written for this
  project. The database is real: the public Olist dataset.
- The router and retrieval benchmarks are small, and the document set is small,
  so those scores are weak evidence on their own.
- SQLite only, no authentication, single-user sessions.
- The hosted demo runs on a ~10% data sample, so answers there differ from the
  full-dataset results.

## Future work

- Replace the synthetic documents with real or data-derived reports, and grow
  the retrieval and router benchmarks.
- Ablation runs (schema only → glossary → few-shot → self-correction) to
  measure what each component contributes.
- Schema pruning and linking for larger databases; hybrid (BM25 + vector)
  retrieval; a Postgres backend.

## Data and credits

Data: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
on Kaggle. Please check the license on the dataset page. The raw files are not
redistributed here; only a small sample database is included for the demo.

## Author

**Alankar Singh Chahal** — B.E. Computer Engineering, Thapar Institute of
Engineering and Technology.

## License

MIT — see [LICENSE](LICENSE).
