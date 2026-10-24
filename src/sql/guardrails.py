"""Never trust generated SQL: AST validation + read-only connection + timeout/row limit."""
import sqlite3
import time

import pandas as pd
import sqlglot
from sqlglot import exp

from src import config

FORBIDDEN = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Command)


def validate_sql(sql: str, max_rows: int = config.MAX_ROWS) -> str:
    """Return a safe SQL string (with LIMIT) or raise ValueError."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="sqlite") if s]
    except sqlglot.errors.SqlglotError as e:
        raise ValueError(f"SQL could not be parsed: {e}") from e
    if len(statements) != 1:
        raise ValueError("Exactly one SQL statement is allowed")
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union)):
        raise ValueError("Only SELECT queries are allowed")
    if tree.find(*FORBIDDEN):
        raise ValueError("Query contains a forbidden operation")
    if not tree.args.get("limit"):
        tree = tree.limit(max_rows)
    return tree.sql(dialect="sqlite")


def run_query(sql: str, db_path: str = config.DB_PATH,
              timeout_s: int = config.SQL_TIMEOUT_S) -> pd.DataFrame:
    """Run SQL on a read-only connection that aborts after timeout_s seconds."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)  # read-only at DB level
    start = time.time()
    con.set_progress_handler(lambda: 1 if time.time() - start > timeout_s else 0, 10000)
    try:
        return pd.read_sql_query(sql, con)
    finally:
        con.close()
