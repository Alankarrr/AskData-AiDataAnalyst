"""Evaluation harness.

Usage:
  python -m eval.run_eval sql    --tag v0
  python -m eval.run_eval rag    --tag v0 [--k 5]
  python -m eval.run_eval router --tag v0
Results are saved to eval/results/<tag>_<mode>.json
"""
import argparse
import json
import time
from pathlib import Path

import pandas as pd

from src import config
from src.llm.providers import get_llm

HERE = Path(__file__).parent


def signature(df: pd.DataFrame):
    """Order-insensitive, rounded fingerprint of a result set (column names ignored)."""
    return sorted(map(tuple, df.round(2).astype(str).values.tolist()))


def exec_match(pred_df, gold_df) -> bool:
    return signature(pred_df) == signature(gold_df)


def eval_sql(tag: str) -> dict:
    from src.sql.generator import text_to_sql
    from src.sql.guardrails import run_query
    from src.sql.schema import get_glossary, get_schema_text

    golden = json.loads((HERE / "golden_sql.json").read_text())
    llm, schema, glossary = get_llm(), get_schema_text(), get_glossary()
    correct = valid = total_retries = 0
    rows = []
    for item in golden:
        gold_df = run_query(item["gold_sql"])
        ok, err, retries, sql = False, None, 0, None
        try:
            sql, pred_df, retries = text_to_sql(item["question"], llm, schema, glossary)
            valid += 1
            total_retries += retries
            ok = pred_df is not None and exec_match(pred_df, gold_df)
        except Exception as e:
            err = str(e)
        correct += ok
        rows.append({"id": item["id"], "correct": bool(ok), "retries": retries,
                     "pred_sql": sql, "error": err})
        print(f"{item['id']}: {'OK ' if ok else 'FAIL'} {item['question']}")
    n = len(golden)
    return {"mode": "sql", "tag": tag, "n": n,
            "execution_accuracy": round(correct / n, 3),
            "valid_sql_rate": round(valid / n, 3),
            "avg_retries": round(total_retries / max(valid, 1), 2), "details": rows}


def eval_rag(tag: str, k: int) -> dict:
    from src.rag.store import retrieve

    golden = json.loads((HERE / "golden_rag.json").read_text())
    hits, rows = 0, []
    for item in golden:
        res = retrieve(item["question"], k=k)
        hit = any(r["source"] == item["expected_source"] for r in res)
        contains = any(item["answer_must_contain"].lower() in r["text"].lower() for r in res)
        hits += hit
        rows.append({"id": item["id"], "hit": hit, "contains_answer": contains})
        print(f"{item['id']}: hit={hit} contains={contains}")
    n = len(golden)
    return {"mode": "rag", "tag": tag, "k": k, "n": n, f"hit_rate@{k}": round(hits / n, 3),
            "details": rows}


def eval_router(tag: str) -> dict:
    from src.agent.router import classify

    golden = json.loads((HERE / "golden_router.json").read_text())
    llm, correct, rows = get_llm(), 0, []
    for item in golden:
        pred = classify(item["question"], llm)
        correct += pred == item["expected"]
        rows.append({**item, "predicted": pred})
        print(f"{item['expected']:5s} -> {pred:5s} {item['question']}")
    return {"mode": "router", "tag": tag, "n": len(golden),
            "routing_accuracy": round(correct / len(golden), 3), "details": rows}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["sql", "rag", "router"])
    ap.add_argument("--tag", default="v0")
    ap.add_argument("--k", type=int, default=config.TOP_K)
    a = ap.parse_args()
    start = time.time()
    result = {"sql": lambda: eval_sql(a.tag), "rag": lambda: eval_rag(a.tag, a.k),
              "router": lambda: eval_router(a.tag)}[a.mode]()
    result["seconds"] = round(time.time() - start, 1)
    out = HERE / "results" / f"{a.tag}_{a.mode}.json"
    out.write_text(json.dumps(result, indent=2))
    summary = {k: v for k, v in result.items() if k != "details"}
    print("\n", json.dumps(summary, indent=2), "\nsaved ->", out)
