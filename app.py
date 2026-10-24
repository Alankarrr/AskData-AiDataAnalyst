"""AskData - Streamlit chat UI.  Run: streamlit run app.py"""
import streamlit as st

from src import config
from src.agent.graph import ask
from src.utils.logging import load_stats

st.set_page_config(page_title="AskData", page_icon="📊", layout="wide")
st.logo("assets/logo.svg")
st.markdown("""<style>
.block-container {padding-top: 2rem; max-width: 900px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg,#161B26,#0E1117);}
.hero h1 {font-size: 2.6rem; background: linear-gradient(90deg,#6C63FF,#00C2A8);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.hero p {color: #9AA3B5; font-size: 1.1rem;}
</style>""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []  # each: role, content (+ extras for assistant)
if "n_questions" not in st.session_state:
    st.session_state.n_questions = 0

EXAMPLES = [
    "Top 5 product categories by revenue in 2017",
    "What is the refund policy for late deliveries?",
    "Why did delivery delays rise in November 2017, and what does the ops report say?",
    "Plot monthly orders for the top 3 states",
]


def report_markdown(msg: dict) -> str:
    parts = [f"# AskData report\n\n**Question:** {msg.get('question', '')}\n\n{msg['content']}\n"]
    if msg.get("sql"):
        parts.append(f"\n## SQL used\n```sql\n{msg['sql']}\n```\n")
    if msg.get("passages"):
        parts.append("\n## Sources\n" + "\n".join(
            f"- {p['source']} (p.{p['page']})" for p in msg["passages"]))
    return "".join(parts)


def render_extras(msg: dict, key: str) -> None:
    if msg.get("figure") is not None:
        st.plotly_chart(msg["figure"], use_container_width=True, key=f"fig-{key}")
    if msg.get("sql"):
        with st.expander("SQL used"):
            st.code(msg["sql"], language="sql")
    if msg.get("table") is not None:
        with st.expander("Raw data"):
            st.dataframe(msg["table"])
            st.download_button("Download CSV", msg["table"].to_csv(index=False),
                               file_name="result.csv", mime="text/csv", key=f"csv-{key}")
    if msg.get("passages"):
        with st.expander("Sources"):
            for p in msg["passages"]:
                st.markdown(f"**{p['source']}** (p.{p['page']}): {p['text'][:300]}...")
    if msg.get("error"):
        with st.expander("Debug details"):
            st.code(msg["error"])
    st.download_button("Export report (.md)", report_markdown(msg),
                       file_name="askdata_report.md", key=f"md-{key}")


with st.sidebar:
    st.markdown("### Try asking")
    for i, ex in enumerate(EXAMPLES):
        if st.button(ex, use_container_width=True, key=f"ex{i}"):
            st.session_state.pending = ex
    st.caption("Data: public Olist e-commerce dataset. Documents are synthetic.")
    with st.expander("Usage stats"):
        stats = load_stats()
        if stats:
            st.json(stats)
        else:
            st.write("No questions logged yet.")
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

if not st.session_state.messages:
    st.markdown('<div class="hero"><h1>AskData</h1>'
                '<p>Your AI data analyst. Ask about sales, delivery and company policies.</p></div>',
                unsafe_allow_html=True)

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            render_extras(m, str(i))

q = st.chat_input("Ask a question...") or st.session_state.pop("pending", None)
if q:
    if st.session_state.n_questions >= config.MAX_QUESTIONS_PER_SESSION:
        st.warning("Session question limit reached. Please refresh the page to continue.")
        st.stop()
    st.session_state.n_questions += 1
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            out = ask(q, history)
        st.markdown(out["answer"])
    st.session_state.messages.append({
        "role": "assistant", "content": out["answer"], "question": q,
        "sql": out.get("sql"), "table": out.get("table"), "figure": out.get("figure"),
        "passages": out.get("passages"), "error": out.get("error")})
    st.rerun()
