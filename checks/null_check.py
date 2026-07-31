"""Checks for null rates exceeding an allowed threshold on given columns."""


def check_nulls(conn, table: str, columns: list, threshold: float = 0.0) -> dict:
    """
    Returns a result dict per column:
      { column: {"null_count": int, "total": int, "null_rate": float, "passed": bool} }

    threshold is the max allowed fraction of nulls (0.0 = zero nulls tolerated).
    """
    total = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    results = {}
    for col in columns:
        null_count = conn.execute(
            f"SELECT count(*) FROM {table} WHERE {col} IS NULL"
        ).fetchone()[0]
        null_rate = null_count / total if total else 0.0
        results[col] = {
            "null_count": null_count,
            "total": total,
            "null_rate": round(null_rate, 4),
            "passed": null_rate <= threshold,
        }
    return results
