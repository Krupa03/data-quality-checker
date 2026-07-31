-- Kimball-style star schema for the order fulfillment data warehouse
-- One fact table (grain: one row per order line item) surrounded by
-- conformed dimension tables. This mirrors the standard DE interview
-- pattern: fact = measurable events, dims = descriptive context.

CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INTEGER PRIMARY KEY,   -- YYYYMMDD surrogate key
    full_date       DATE,
    day_of_week     VARCHAR,
    month           INTEGER,
    month_name      VARCHAR,
    quarter         INTEGER,
    year            INTEGER,
    is_weekend      BOOLEAN
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key    INTEGER PRIMARY KEY,   -- surrogate key
    customer_id     VARCHAR,               -- natural/business key
    customer_name   VARCHAR,
    segment         VARCHAR,               -- e.g. Consumer / Corporate / SMB
    signup_date     DATE
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key     INTEGER PRIMARY KEY,
    product_id      VARCHAR,
    product_name    VARCHAR,
    category        VARCHAR,
    unit_price      DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS dim_geography (
    geography_key   INTEGER PRIMARY KEY,
    city            VARCHAR,
    state           VARCHAR,
    country         VARCHAR,
    region          VARCHAR
);

-- Note: fact_orders does NOT declare foreign key constraints, even though
-- date_key/customer_key/product_key/geography_key are logically FKs to the
-- dimension tables above. This is deliberate and realistic: most cloud
-- data warehouses (Snowflake, BigQuery, Redshift) don't enforce FK
-- constraints at the engine level for performance reasons -- they're
-- declared for documentation/lineage tools but not physically enforced.
-- That's exactly why a referential integrity *check* like the one in
-- this project (checks/referential_integrity.py) is needed in real
-- pipelines: nothing stops an orphaned row from landing in the fact
-- table, so you have to detect it after the fact.
-- order_line_id is NOT declared PRIMARY KEY for the same reason as above:
-- warehouses generally don't enforce uniqueness constraints on load, so a
-- duplicate-detection check (checks/duplicate_check.py) has to do that
-- job instead of relying on the engine to reject bad rows.
CREATE TABLE IF NOT EXISTS fact_orders (
    order_line_id   INTEGER,               -- fact grain key
    order_id        VARCHAR,
    date_key        INTEGER,               -- logical FK -> dim_date.date_key
    customer_key    INTEGER,               -- logical FK -> dim_customer.customer_key
    product_key     INTEGER,               -- logical FK -> dim_product.product_key
    geography_key   INTEGER,               -- logical FK -> dim_geography.geography_key
    quantity        INTEGER,
    unit_price      DECIMAL(10,2),
    line_total      DECIMAL(12,2),
    loaded_at       TIMESTAMP DEFAULT (current_timestamp AT TIME ZONE 'UTC')  -- used by the freshness check; explicit UTC conversion avoids a bug where DuckDB's plain current_timestamp default uses the OS's local timezone, which corrupts freshness math on machines outside UTC (e.g. IST, UTC+5:30)
);
