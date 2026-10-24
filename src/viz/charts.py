"""LLM proposes a JSON chart spec; we render it ourselves. Never execute LLM code."""
import json
import re

import plotly.express as px

from src import config

CHARTS = {"bar": px.bar, "line": px.line, "scatter": px.scatter}


def make_chart(question: str, df, llm):
    if df is None or len(df) < 2:
        return None
    prompt = (f"Question: {question}\nColumns: {list(df.columns)}\n"
              f"Sample rows: {df.head(3).to_dict('records')}")
    try:
        raw = llm.generate(prompt, system=config.read_prompt("chart.txt"))
        m = re.search(r"\{.*\}", raw, re.S)
        spec = json.loads(m.group(0))
        if spec.get("chart") not in CHARTS:
            return None
        if spec["x"] not in df.columns or spec["y"] not in df.columns:
            return None
        color = spec.get("color") if spec.get("color") in df.columns else None
        return CHARTS[spec["chart"]](df, x=spec["x"], y=spec["y"], color=color,
                                     title=spec.get("title", ""), template="plotly_dark")
    except Exception:
        return None  # fall back to table only
