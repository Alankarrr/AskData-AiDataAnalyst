"""Create a small ~10% sampled DB for deployment.  Run: python -m scripts.make_sample_db"""
import sqlite3
from pathlib import Path

from src import config

OUT = str(Path(config.ROOT / "data" / "olist_sample.db"))


def main() -> None:
    Path(OUT).unlink(missing_ok=True)
    con = sqlite3.connect(OUT)
    con.execute(f"ATTACH DATABASE '{config.DB_PATH}' AS src")
    q = [
        "CREATE TABLE olist_orders_dataset AS SELECT * FROM src.olist_orders_dataset WHERE rowid % 10 = 0",
        "CREATE TABLE olist_order_items_dataset AS SELECT * FROM src.olist_order_items_dataset WHERE order_id IN (SELECT order_id FROM olist_orders_dataset)",
        "CREATE TABLE olist_order_payments_dataset AS SELECT * FROM src.olist_order_payments_dataset WHERE order_id IN (SELECT order_id FROM olist_orders_dataset)",
        "CREATE TABLE olist_order_reviews_dataset AS SELECT * FROM src.olist_order_reviews_dataset WHERE order_id IN (SELECT order_id FROM olist_orders_dataset)",
        "CREATE TABLE olist_customers_dataset AS SELECT * FROM src.olist_customers_dataset WHERE customer_id IN (SELECT customer_id FROM olist_orders_dataset)",
        "CREATE TABLE olist_products_dataset AS SELECT * FROM src.olist_products_dataset WHERE product_id IN (SELECT product_id FROM olist_order_items_dataset)",
        "CREATE TABLE olist_sellers_dataset AS SELECT * FROM src.olist_sellers_dataset WHERE seller_id IN (SELECT seller_id FROM olist_order_items_dataset)",
        "CREATE TABLE product_category_name_translation AS SELECT * FROM src.product_category_name_translation",
    ]
    for stmt in q:
        con.execute(stmt)
    con.commit()
    con.execute("DETACH DATABASE src")
    con.execute("VACUUM")
    con.close()
    print("sample DB written to", OUT, "- set DB_PATH to it or rename to data/olist.db for deployment")


if __name__ == "__main__":
    main()
