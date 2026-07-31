"""
Unit tests for each quality check, using a fast in-memory DuckDB connection
with small fixture tables -- no dependency on the sample data generator or
any live warehouse connection.
"""

import duckdb
import pytest

from checks.null_check import check_nulls
from checks.duplicate_check import check_duplicates
from checks.referential_integrity import check_referential_integrity
from checks.schema_drift import check_schema_drift


@pytest.fixture
def conn():
    c = duckdb.connect(":memory:")
    c.execute("""
        CREATE TABLE dim_customer (customer_key INTEGER, name VARCHAR)
    """)
    c.execute("INSERT INTO dim_customer VALUES (1, 'Alice'), (2, 'Bob')")

    c.execute("""
        CREATE TABLE fact_orders (
            order_line_id INTEGER,
            customer_key INTEGER,
            order_id VARCHAR,
            quantity INTEGER
        )
    """)
    c.execute("""
        INSERT INTO fact_orders VALUES
            (1, 1, 'ORD-1', 2),
            (2, 2, 'ORD-2', NULL),
            (3, 99, 'ORD-3', 1),
            (3, 99, 'ORD-3', 1)
    """)  # row 2 has a null qty, row 3 is duplicated, customer_key=99 is orphaned
    return c


def test_check_nulls_detects_null_quantity(conn):
    result = check_nulls(conn, "fact_orders", ["quantity"], threshold=0.0)
    assert result["quantity"]["null_count"] == 1
    assert result["quantity"]["passed"] is False


def test_check_nulls_passes_when_no_nulls(conn):
    result = check_nulls(conn, "fact_orders", ["order_id"], threshold=0.0)
    assert result["order_id"]["null_count"] == 0
    assert result["order_id"]["passed"] is True


def test_check_duplicates_detects_duplicate_key(conn):
    result = check_duplicates(conn, "fact_orders", ["order_line_id"])
    assert result["duplicate_key_count"] == 1
    assert result["passed"] is False


def test_check_referential_integrity_detects_orphan(conn):
    result = check_referential_integrity(
        conn, "fact_orders", "customer_key", "dim_customer", "customer_key"
    )
    assert result["orphan_count"] == 2  # both rows with customer_key=99
    assert result["passed"] is False


def test_check_referential_integrity_passes_with_valid_keys(conn):
    conn.execute("DELETE FROM fact_orders WHERE customer_key = 99")
    result = check_referential_integrity(
        conn, "fact_orders", "customer_key", "dim_customer", "customer_key"
    )
    assert result["orphan_count"] == 0
    assert result["passed"] is True


def test_check_schema_drift_detects_added_column(conn):
    expected = {"order_line_id", "customer_key", "order_id"}  # missing "quantity"
    result = check_schema_drift(conn, "fact_orders", expected)
    assert "quantity" in result["added_columns"]
    assert result["passed"] is False


def test_check_schema_drift_passes_when_matching(conn):
    expected = {"order_line_id", "customer_key", "order_id", "quantity"}
    result = check_schema_drift(conn, "fact_orders", expected)
    assert result["passed"] is True
