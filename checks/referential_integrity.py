"""Checks that every foreign key in a fact table has a matching dimension row.

This is the classic star-schema sanity check: an orphaned fact row (FK
pointing to a dim row that doesn't exist) means broken joins downstream --
BI dashboards silently drop or mis-attribute those rows.
"""


def check_referential_integrity(
    conn, fact_table: str, fk_column: str, dim_table: str, pk_column: str
) -> dict:
    query = f"""
        SELECT count(*)
        FROM {fact_table} f
        LEFT JOIN {dim_table} d ON f.{fk_column} = d.{pk_column}
        WHERE d.{pk_column} IS NULL AND f.{fk_column} IS NOT NULL
    """
    orphan_count = conn.execute(query).fetchone()[0]
    return {
        "fact_table": fact_table,
        "fk_column": fk_column,
        "dim_table": dim_table,
        "orphan_count": orphan_count,
        "passed": orphan_count == 0,
    }
