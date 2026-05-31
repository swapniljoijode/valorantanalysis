"""Load pipeline DataFrames into the PostgreSQL data warehouse (raw layer).

This is the landing step of the ELT flow: pandas DataFrames produced by the
pipeline are written as-is into a `raw` schema. Downstream cleaning and modelling
is the job of dbt (Phase 2), so this module intentionally does no transformation.
"""

import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from source import logging, CustomException

load_dotenv()

DEFAULT_SCHEMA = os.getenv("RAW_SCHEMA", "raw")

# Postgres caps a single statement at 65535 bind parameters. With method="multi"
# pandas batches `chunksize` rows per INSERT, so chunksize * n_cols must stay under
# that ceiling. We derive a safe chunksize per table from its column count.
_MAX_BIND_PARAMS = 65535
_MAX_CHUNKSIZE = 5000


def get_engine() -> Engine:
    """Build a SQLAlchemy engine from environment variables (see .env.example)."""
    user = os.getenv("POSTGRES_USER", "valorant")
    password = os.getenv("POSTGRES_PASSWORD", "valorant")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "valorant")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url, pool_pre_ping=True)


def ensure_schema(engine: Engine, schema: str = DEFAULT_SCHEMA) -> None:
    """Create the target schema if it does not already exist."""
    try:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        logging.info(f"Ensured schema '{schema}' exists")
    except Exception as e:
        raise CustomException(e, sys)


def _safe_chunksize(n_cols: int) -> int:
    n_cols = max(n_cols, 1)
    return max(1, min(_MAX_CHUNKSIZE, _MAX_BIND_PARAMS // (n_cols + 1)))


def _drop_table_cascade(engine: Engine, table_name: str, schema: str) -> None:
    """Drop a raw table together with anything that depends on it.

    pandas' ``if_exists="replace"`` emits a plain ``DROP TABLE`` which fails once
    dbt has built staging views on top of the raw layer
    (``DependentObjectsStillExist``). The raw layer is owned by this loader and the
    dbt views/marts are derived artifacts, so a reload legitimately invalidates them
    — we drop with CASCADE and let ``dbt build`` recreate the downstream models.
    """
    with engine.begin() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS "{schema}"."{table_name}" CASCADE'))


def load_dataframe(
    df: pd.DataFrame,
    table_name: str,
    engine: Engine,
    schema: str = DEFAULT_SCHEMA,
    if_exists: str = "replace",
) -> int:
    """Write a single DataFrame to `schema.table_name`. Returns rows written.

    Uses method="multi" so pandas converts NaN/NaT to SQL NULL via parameter
    binding (a plain COPY would serialise NaN as the literal text 'nan').
    """
    try:
        if if_exists == "replace":
            # Pre-drop with CASCADE so dependent dbt views don't block the reload,
            # then create the table fresh (table no longer exists, so "replace" just
            # creates). This keeps raw schema evolution working (e.g. new columns).
            _drop_table_cascade(engine, table_name, schema)
        df.to_sql(
            table_name,
            engine,
            schema=schema,
            if_exists=if_exists,
            index=False,
            method="multi",
            chunksize=_safe_chunksize(len(df.columns)),
        )
        logging.info(
            f"Loaded {len(df)} rows into {schema}.{table_name} ({len(df.columns)} cols)"
        )
        return len(df)
    except Exception as e:
        raise CustomException(e, sys)


def load_all(
    dataframes: dict,
    engine: Engine = None,
    schema: str = DEFAULT_SCHEMA,
    if_exists: str = "replace",
) -> dict:
    """Load a {table_name: DataFrame} mapping into the warehouse.

    Returns a {table_name: rows_written} report.
    """
    if engine is None:
        engine = get_engine()

    ensure_schema(engine, schema)

    report = {}
    logging.info(f"Loading {len(dataframes)} tables into schema '{schema}'")
    for table_name, df in dataframes.items():
        report[table_name] = load_dataframe(df, table_name, engine, schema, if_exists)

    total = sum(report.values())
    logging.info(f"Warehouse load complete: {len(report)} tables, {total} total rows")
    return report
