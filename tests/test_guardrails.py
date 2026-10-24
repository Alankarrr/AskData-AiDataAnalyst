import sqlite3

import pytest

from src.sql.guardrails import run_query, validate_sql

ATTACKS = [
    "DROP TABLE olist_orders_dataset",
    "DELETE FROM olist_orders_dataset",
    "UPDATE olist_orders_dataset SET order_status = 'x'",
    "INSERT INTO olist_orders_dataset VALUES (1)",
    "SELECT 1; DROP TABLE olist_orders_dataset",
    "SELECT 1; DELETE FROM olist_orders_dataset",
    "CREATE TABLE evil (a int)",
    "PRAGMA table_info(olist_orders_dataset)",
    "ATTACH DATABASE 'x.db' AS x",
    "drOp TaBLe olist_orders_dataset",
    "WITH x AS (SELECT 1) DELETE FROM olist_orders_dataset",
]


@pytest.mark.parametrize("sql", ATTACKS)
def test_blocks_attacks(sql):
    with pytest.raises(ValueError):
        validate_sql(sql)


def test_adds_limit():
    assert "LIMIT" in validate_sql("SELECT * FROM orders").upper()


def test_keeps_existing_limit():
    out = validate_sql("SELECT * FROM orders LIMIT 5")
    assert out.upper().count("LIMIT") == 1 and "5" in out


def test_comment_does_not_hide_second_statement():
    with pytest.raises(ValueError):
        validate_sql("SELECT 1; -- harmless\nDROP TABLE orders")


def test_allows_cte_and_join():
    sql = ("WITH t AS (SELECT a FROM x) SELECT t.a FROM t JOIN y ON y.a = t.a")
    assert validate_sql(sql).upper().startswith("WITH")


def test_readonly_connection_rejects_writes(tmp_path):
    db = tmp_path / "t.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE a (x INTEGER)")
    con.commit()
    con.close()
    with pytest.raises(Exception):
        run_query("INSERT INTO a VALUES (1)", db_path=str(db))


def test_timeout_triggers(tmp_path):
    db = tmp_path / "t.db"
    sqlite3.connect(db).close()
    heavy = ("WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c WHERE x < 100000000) "
             "SELECT COUNT(*) FROM c")
    with pytest.raises(Exception):
        run_query(heavy, db_path=str(db), timeout_s=1)
