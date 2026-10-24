"""Text-to-SQL with a self-correction loop."""
import re

import pandas as pd

from src import config
from src.sql.guardrails import run_query, validate_sql
from src.sql.schema import get_few_shot


def extract_sql(text: str) -> str:
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    return (m.group(1) if m else text).strip().rstrip(";")


def build_system_prompt(schema: str, glossary: str) -> str:
    return (config.read_prompt("sql_system.txt")
            .replace("{schema}", schema)
            .replace("{glossary}", glossary)
            .replace("{few_shot_examples}", get_few_shot()))


def build_user_prompt(question: str, last_sql: str | None, error: str | None) -> str:
    prompt = f"Question: {question}\nReturn only the SQL inside a ```sql block."
    if last_sql and error:
        prompt += (f"\n\nYour previous query:\n```sql\n{last_sql}\n```\n"
                   f"failed with this error:\n{error}\n"
                   "Fix it and return only the corrected SQL.")
    return prompt


def text_to_sql(question: str, llm, schema: str, glossary: str,
                max_retries: int = config.MAX_RETRIES
                ) -> tuple[str | None, pd.DataFrame | None, int]:
    """Return (sql, dataframe, retries_used). (None, None, n) means CANNOT_ANSWER."""
    system = build_system_prompt(schema, glossary)
    error, last_sql = None, None
    for attempt in range(max_retries):
        raw = llm.generate(build_user_prompt(question, last_sql, error), system=system)
        if "CANNOT_ANSWER" in raw:
            return None, None, attempt
        last_sql = extract_sql(raw)
        try:
            safe_sql = validate_sql(last_sql)
            return safe_sql, run_query(safe_sql), attempt
        except Exception as e:  # syntax error, bad column, blocked SQL, timeout
            error = str(e)
    raise RuntimeError(f"Could not produce valid SQL after {max_retries} tries: {error}")
