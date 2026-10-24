"""Load Olist CSV files from data/raw into SQLite.  Run: python -m scripts.load_data"""
import sqlite3
from pathlib import Path

import pandas as pd

from src import config

INDEXES = [
    ("olist_orders_dataset", "order_id"), ("olist_orders_dataset", "customer_id"),
    ("olist_order_items_dataset", "order_id"), ("olist_order_items_dataset", "product_id"),
    ("olist_order_items_dataset", "seller_id"), ("olist_order_payments_dataset", "order_id"),
    ("olist_order_reviews_dataset", "order_id"), ("olist_products_dataset", "product_id"),
    ("olist_customers_dataset", "customer_id"),
]


def main() -> None:
    csvs = sorted(Path(config.ROOT / "data" / "raw").glob("*.csv"))
    if not csvs:
        raise SystemExit("No CSV files in data/raw. Download the Olist dataset from Kaggle first.")
    con = sqlite3.connect(config.DB_PATH)
    for csv in csvs:
        df = pd.read_csv(csv)
        table = csv.stem
        df.to_sql(table, con, if_exists="replace", index=False)
        print(f"loaded {table}: {len(df):,} rows")
    cur = con.cursor()
    existing = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table, col in INDEXES:
        if table in existing:
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_{col} ON {table}({col})")
    con.commit()
    con.close()
    print("done ->", config.DB_PATH)


if __name__ == "__main__":
    main()
