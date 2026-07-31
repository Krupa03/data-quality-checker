"""Checks that data was loaded recently enough (freshness SLA)."""

from datetime import datetime, timezone


def check_freshness(
    conn, table: str, timestamp_column: str, max_age_hours: float = 24.0
) -> dict:
    row = conn.execute(f"SELECT max({timestamp_column}) FROM {table}").fetchone()
    last_loaded = row[0]
    if last_loaded is None:
        return {"passed": False, "reason": "no rows found / null timestamp"}

    now = datetime.now(timezone.utc)
    if last_loaded.tzinfo:
        last_loaded_utc = last_loaded
    else:
        last_loaded_utc = last_loaded.replace(tzinfo=timezone.utc)
    age_hours = (now - last_loaded_utc).total_seconds() / 3600

    return {
        "last_loaded": str(last_loaded),
        "age_hours": round(age_hours, 2),
        "max_age_hours": max_age_hours,
        "passed": age_hours <= max_age_hours,
    }
