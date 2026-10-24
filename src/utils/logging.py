import json
import time

import pandas as pd

from src import config


def log_event(**fields) -> None:
    config.LOG_PATH.parent.mkdir(exist_ok=True)
    with open(config.LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **fields}, default=str) + "\n")


def load_stats() -> dict | None:
    if not config.LOG_PATH.exists():
        return None
    df = pd.read_json(config.LOG_PATH, lines=True)
    if df.empty:
        return None
    return {
        "questions": len(df),
        "routes": df["route"].value_counts().to_dict(),
        "avg_latency_s": round(float(df["latency_s"].mean()), 2),
        "p95_latency_s": round(float(df["latency_s"].quantile(0.95)), 2),
        "retry_rate": round(float((df["retries"].fillna(0) > 0).mean()), 3),
        "cache_hit_rate": round(float(df["cached"].fillna(False).astype(bool).mean()), 3),
    }
