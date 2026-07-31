"""Checks for duplicate rows on a given key (or full-row duplicates)."""


def check_duplicates(conn, table: str, key_columns: list) -> dict:
    """
    Returns:
      {"duplicate_key_count": int, "sample_keys": list, "passed": bool}

    duplicate_key_count is the number of key values that appear more than once.
    """
    keys = ", ".join(key_columns)
    query = f"""
        SELECT {keys}, count(*) as cnt
        FROM {table}
        GROUP BY {keys}
        HAVING count(*) > 1
    """
    dupes = conn.execute(query).fetchall()
    return {
        "duplicate_key_count": len(dupes),
        "sample_keys": dupes[:5],
        "passed": len(dupes) == 0,
    }
