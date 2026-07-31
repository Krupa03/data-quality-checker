"""
Thin wrapper around DuckDB acting as our data warehouse connection layer.

Why DuckDB: it's a genuine OLAP / columnar warehouse engine (not just a
toy database) with zero signup friction, which makes it a good stand-in
while we're still working around Snowflake trial UI issues. Swapping this
module out for `snowflake-connector-python` later is a same-shape change:
every function here just needs to return DuckDB's own connection object,
or something that speaks the same execute()/fetchdf() interface.
"""

from pathlib import Path
import duckdb

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.duckdb"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    """Open (or create) the warehouse database file."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def initialize_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the star schema tables if they don't already exist."""
    ddl = SCHEMA_PATH.read_text()
    conn.execute(ddl)


def table_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    result = conn.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = ?",
        [table_name],
    ).fetchone()
    return result[0] > 0
