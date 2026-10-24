import sqlite3
from functools import lru_cache

from src import config


@lru_cache(maxsize=1)
def get_schema_text(db_path: str = config.DB_PATH, sample_rows: int = 3) -> str:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = con.cursor()
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    parts = []
    for t in tables:
        cols = cur.execute(f'PRAGMA table_info("{t}")').fetchall()
        col_txt = ", ".join(f"{c[1]} {c[2]}" for c in cols)
        rows = cur.execute(f'SELECT * FROM "{t}" LIMIT {sample_rows}').fetchall()
        parts.append(f"TABLE {t} ({col_txt})\nSAMPLE ROWS: {rows}")
    con.close()
    return "\n\n".join(parts)


@lru_cache(maxsize=1)
def get_glossary() -> str:
    return config.GLOSSARY_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def get_few_shot() -> str:
    p = config.PROMPTS_DIR / "few_shot.txt"
    return p.read_text(encoding="utf-8") if p.exists() else ""
