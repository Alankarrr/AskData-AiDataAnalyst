"""LangGraph wiring: condense -> route -> (sql -> chart)? -> (rag)? -> answer."""
import time
from functools import lru_cache
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src import config
from src.agent.memory import condense
from src.agent.router import classify
from src.agent.synthesizer import synthesize
from src.llm.providers import get_llm
from src.sql.generator import text_to_sql
from src.sql.schema import get_glossary, get_schema_text
from src.utils import cache
from src.utils.logging import log_event
from src.viz.charts import make_chart


class AgentState(TypedDict, total=False):
    question: str
    standalone: str
    history: list
    route: str
    sql: str
    table: Any  # pandas DataFrame
    passages: list
    figure: Any
    answer: str
    error: str
    retries: int


def condense_node(s):
    return {"standalone": condense(s["question"], s.get("history", []), get_llm())}


def route_node(s):
    return {"route": classify(s["standalone"], get_llm())}


def sql_node(s):
    try:
        sql, df, retries = text_to_sql(
            s["standalone"], get_llm(), get_schema_text(), get_glossary())
    except RuntimeError as e:
        return {"sql": "", "table": None, "error": f"SQL step failed: {e}", "retries": config.MAX_RETRIES}
    if sql is None:
        return {"sql": "", "table": None, "retries": retries,
                "error": "The database does not contain the information needed for this question."}
    return {"sql": sql, "table": df, "retries": retries}


def chart_node(s):
    return {"figure": make_chart(s["standalone"], s.get("table"), get_llm())}


def rag_node(s):
    from src.rag.store import retrieve  # lazy: avoids loading embedding model for SQL-only use
    try:
        return {"passages": retrieve(s["standalone"], k=config.TOP_K)}
    except Exception as e:
        return {"passages": [], "error": f"Document search failed: {e}"}


def answer_node(s):
    return {"answer": synthesize(s, get_llm())}


@lru_cache(maxsize=1)
def build_graph():
    g = StateGraph(AgentState)
    for name, fn in [("condense", condense_node), ("route", route_node), ("sql", sql_node),
                     ("chart", chart_node), ("rag", rag_node), ("answer", answer_node)]:
        g.add_node(name, fn)
    g.set_entry_point("condense")
    g.add_edge("condense", "route")
    g.add_conditional_edges("route", lambda s: s["route"],
                            {"SQL": "sql", "BOTH": "sql", "DOCS": "rag", "CHAT": "answer"})
    g.add_edge("sql", "chart")
    g.add_conditional_edges("chart", lambda s: "rag" if s["route"] == "BOTH" else "answer",
                            {"rag": "rag", "answer": "answer"})
    g.add_edge("rag", "answer")
    g.add_edge("answer", END)
    return g.compile()


def ask(question: str, history: list[dict] | None = None) -> dict:
    """Public entry point used by the UI and eval: cache + logging around the graph."""
    history = history or []
    if not history:  # follow-ups depend on context, so only cache stand-alone questions
        hit = cache.get(question)
        if hit:
            log_event(question=question, route=hit.get("route"), sql=hit.get("sql"),
                      retries=0, latency_s=0.0, cached=True)
            return hit
    start = time.time()
    try:
        out = build_graph().invoke({"question": question, "history": history[-6:]})
    except Exception as e:
        log_event(question=question, route="ERROR", sql=None, retries=0,
                  latency_s=round(time.time() - start, 2), cached=False, error=str(e))
        return {"answer": "Sorry, something went wrong while answering. Please try again "
                          "in a moment.", "route": "ERROR", "error": str(e)}
    latency = round(time.time() - start, 2)
    log_event(question=question, route=out.get("route"), sql=out.get("sql"),
              retries=out.get("retries", 0), latency_s=latency, cached=False,
              tokens=getattr(get_llm(), "total_tokens", None))
    if not history:
        cache.put(question, out)
    return out
