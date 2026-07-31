"""
Generates synthetic order data and loads it into the DuckDB warehouse
using the star schema defined in warehouse/schema.sql.

This is intentionally synthetic (not scraped/downloaded) so the project
has no external data dependency and no licensing questions -- run it
anywhere, anytime, offline.
"""

import random
from datetime import date, timedelta

import pandas as pd

from warehouse.duckdb_connector import get_connection, initialize_schema

random.seed(42)

CATEGORIES = ["Electronics", "Home & Kitchen", "Apparel", "Books", "Sports"]
SEGMENTS = ["Consumer", "Corporate", "SMB"]
REGIONS = {
    "Ahmedabad": ("Gujarat", "India", "APAC"),
    "Mumbai": ("Maharashtra", "India", "APAC"),
    "Dublin": ("Leinster", "Ireland", "EU"),
    "Warsaw": ("Masovian", "Poland", "EU"),
    "Toronto": ("Ontario", "Canada", "NA"),
}


def _date_key(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def build_dim_date(start: date, days: int) -> pd.DataFrame:
    rows = []
    for i in range(days):
        d = start + timedelta(days=i)
        rows.append(
            {
                "date_key": _date_key(d),
                "full_date": d,
                "day_of_week": d.strftime("%A"),
                "month": d.month,
                "month_name": d.strftime("%B"),
                "quarter": (d.month - 1) // 3 + 1,
                "year": d.year,
                "is_weekend": d.weekday() >= 5,
            }
        )
    return pd.DataFrame(rows)


def build_dim_customer(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "customer_key": i,
                "customer_id": f"CUST-{i:05d}",
                "customer_name": f"Customer {i}",
                "segment": random.choice(SEGMENTS),
                "signup_date": date(2024, 1, 1) + timedelta(days=random.randint(0, 500)),
            }
            for i in range(1, n + 1)
        ]
    )


def build_dim_product(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "product_key": i,
                "product_id": f"PROD-{i:04d}",
                "product_name": f"Product {i}",
                "category": random.choice(CATEGORIES),
                "unit_price": round(random.uniform(5, 500), 2),
            }
            for i in range(1, n + 1)
        ]
    )


def build_dim_geography() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "geography_key": i,
                "city": city,
                "state": state,
                "country": country,
                "region": region,
            }
            for i, (city, (state, country, region)) in enumerate(REGIONS.items(), start=1)
        ]
    )


def build_fact_orders(
    n: int, n_customers: int, n_products: int, n_geo: int,
    date_keys: list, inject_bad_rows: bool = True
) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        qty = random.randint(1, 5)
        price = round(random.uniform(5, 500), 2)
        rows.append(
            {
                "order_line_id": i,
                "order_id": f"ORD-{(i // 3) + 1:05d}",
                "date_key": random.choice(date_keys),
                "customer_key": random.randint(1, n_customers),
                "product_key": random.randint(1, n_products),
                "geography_key": random.randint(1, n_geo),
                "quantity": qty,
                "unit_price": price,
                "line_total": round(qty * price, 2),
            }
        )

    if inject_bad_rows:
        # Deliberately seed a few data quality problems so the checks
        # have something real to catch -- this is what makes the demo
        # convincing rather than "checker runs, finds nothing, ever."
        rows[3]["quantity"] = None                     # null check should catch this
        rows[7]["customer_key"] = 99999                # referential integrity violation
        rows.append(dict(rows[10]))                    # exact duplicate row
        rows[-1]["order_line_id"] = rows[10]["order_line_id"]

    return pd.DataFrame(rows)


def main():
    conn = get_connection()
    initialize_schema(conn)

    dim_date = build_dim_date(date(2026, 1, 1), 120)
    dim_customer = build_dim_customer(50)
    dim_product = build_dim_product(30)
    dim_geography = build_dim_geography()
    fact_orders = build_fact_orders(
        n=500,
        n_customers=50,
        n_products=30,
        n_geo=len(dim_geography),
        date_keys=dim_date["date_key"].tolist(),
    )

    conn.execute("DELETE FROM fact_orders")
    conn.execute("DELETE FROM dim_date")
    conn.execute("DELETE FROM dim_customer")
    conn.execute("DELETE FROM dim_product")
    conn.execute("DELETE FROM dim_geography")

    conn.register("dim_date_df", dim_date)
    conn.execute("INSERT INTO dim_date SELECT * FROM dim_date_df")
    conn.register("dim_customer_df", dim_customer)
    conn.execute("INSERT INTO dim_customer SELECT * FROM dim_customer_df")
    conn.register("dim_product_df", dim_product)
    conn.execute("INSERT INTO dim_product SELECT * FROM dim_product_df")
    conn.register("dim_geography_df", dim_geography)
    conn.execute("INSERT INTO dim_geography SELECT * FROM dim_geography_df")
    conn.register("fact_orders_df", fact_orders)
    conn.execute(
        "INSERT INTO fact_orders "
        "(order_line_id, order_id, date_key, customer_key, product_key, "
        " geography_key, quantity, unit_price, line_total) "
        "SELECT order_line_id, order_id, date_key, customer_key, product_key, "
        "       geography_key, quantity, unit_price, line_total FROM fact_orders_df"
    )

    print(f"Loaded {len(dim_date)} dim_date rows")
    print(f"Loaded {len(dim_customer)} dim_customer rows")
    print(f"Loaded {len(dim_product)} dim_product rows")
    print(f"Loaded {len(dim_geography)} dim_geography rows")
    print(f"Loaded {len(fact_orders)} fact_orders rows (with seeded quality issues)")


if __name__ == "__main__":
    main()
