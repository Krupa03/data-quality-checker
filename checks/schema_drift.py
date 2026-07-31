"""Detects schema drift: columns added/removed since the last known-good snapshot."""


def get_current_columns(conn, table: str) -> set:
    rows = conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
        [table],
    ).fetchall()
    return {r[0] for r in rows}


def check_schema_drift(conn, table: str, expected_columns: set) -> dict:
    current = get_current_columns(conn, table)
    added = current - expected_columns
    removed = expected_columns - current
    return {
        "added_columns": sorted(added),
        "removed_columns": sorted(removed),
        "passed": not added and not removed,
    }
