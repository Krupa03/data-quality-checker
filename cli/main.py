"""
Data Quality Checker CLI.

Usage:
    python -m cli.main load-sample-data
    python -m cli.main run --table fact_orders
"""

import json
import sys
from datetime import datetime, timezone

import click

from warehouse.duckdb_connector import get_connection, table_exists
from checks.null_check import check_nulls
from checks.duplicate_check import check_duplicates
from checks.referential_integrity import check_referential_integrity
from checks.freshness_check import check_freshness
from checks.schema_drift import check_schema_drift

EXPECTED_FACT_ORDERS_COLUMNS = {
    "order_line_id", "order_id", "date_key", "customer_key", "product_key",
    "geography_key", "quantity", "unit_price", "line_total", "loaded_at",
}


@click.group()
def cli():
    """Data warehouse quality checker."""
    pass


@cli.command("load-sample-data")
def load_sample_data():
    """Generate and load synthetic star-schema data into the DuckDB warehouse."""
    from data.generate_sample_data import main as generate_main
    generate_main()


@cli.command("run")
@click.option("--table", default="fact_orders", help="Fact table to validate.")
@click.option("--max-age-hours", default=24.0, help="Freshness SLA in hours.")
@click.option("--fail-on-error/--no-fail-on-error", default=True,
              help="Exit non-zero if any check fails (useful for CI).")
def run(table, max_age_hours, fail_on_error):
    """Run the full quality check suite against a warehouse table."""
    conn = get_connection()

    if not table_exists(conn, table):
        click.echo(f"Table '{table}' does not exist. Run 'load-sample-data' first.", err=True)
        sys.exit(1)

    report = {
        "table": table,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    report["checks"]["nulls"] = check_nulls(
        conn, table, ["order_id", "date_key", "customer_key", "quantity"]
    )
    report["checks"]["duplicates"] = check_duplicates(conn, table, ["order_line_id"])
    report["checks"]["referential_integrity"] = check_referential_integrity(
        conn, table, "customer_key", "dim_customer", "customer_key"
    )
    report["checks"]["freshness"] = check_freshness(
        conn, table, "loaded_at", max_age_hours=max_age_hours
    )
    report["checks"]["schema_drift"] = check_schema_drift(
        conn, table, EXPECTED_FACT_ORDERS_COLUMNS
    )

    all_passed = _all_checks_passed(report["checks"])
    report["overall_passed"] = all_passed

    click.echo(json.dumps(report, indent=2, default=str))

    if fail_on_error and not all_passed:
        sys.exit(1)


def _all_checks_passed(checks: dict) -> bool:
    for check_name, result in checks.items():
        if check_name == "nulls":
            if not all(col_result["passed"] for col_result in result.values()):
                return False
        else:
            if not result.get("passed", False):
                return False
    return True


if __name__ == "__main__":
    cli()
