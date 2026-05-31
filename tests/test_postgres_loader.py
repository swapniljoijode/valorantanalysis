"""Tests for the PostgreSQL warehouse loader.

These run against a live Postgres (e.g. the docker-compose service). If Postgres
is unreachable the whole module is skipped so the suite stays green without it.

All tests use a throwaway `loader_test` schema, dropped at the end, so they never
touch the real `raw` schema.
"""

import glob
import os

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import text

from source.components.warehouse import postgres_loader as pl

TEST_SCHEMA = "loader_test"


@pytest.fixture(scope="module")
def engine():
    eng = pl.get_engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - env dependent
        pytest.skip(f"Postgres not reachable ({exc}). Run `docker compose up -d`.")
    pl.ensure_schema(eng, TEST_SCHEMA)
    yield eng
    with eng.begin() as conn:
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))


def _count(engine, table):
    sql = text(f'SELECT count(*) FROM "{TEST_SCHEMA}"."{table}"')
    with engine.connect() as conn:
        return conn.execute(sql).scalar()


def test_connection(engine):
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1


def test_ensure_schema_is_idempotent(engine):
    pl.ensure_schema(engine, TEST_SCHEMA)
    pl.ensure_schema(engine, TEST_SCHEMA)  # second call must not raise
    sql = text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :s"
    )
    with engine.connect() as conn:
        assert conn.execute(sql, {"s": TEST_SCHEMA}).fetchone() is not None


def test_load_dataframe_roundtrip(engine):
    df = pd.DataFrame(
        {"id": [1, 2, 3], "name": ["jett", "sage", "omen"], "score": [10.5, 20.0, 30.25]}
    )
    rows = pl.load_dataframe(df, "roundtrip", engine, schema=TEST_SCHEMA)
    assert rows == 3

    back = pd.read_sql(
        text(f'SELECT * FROM "{TEST_SCHEMA}".roundtrip ORDER BY id'), engine
    )
    assert len(back) == 3
    assert list(back["name"]) == ["jett", "sage", "omen"]
    assert back["score"].sum() == pytest.approx(60.75)


def test_nan_becomes_null(engine):
    df = pd.DataFrame({"id": [1, 2, 3], "val": [1.5, np.nan, 3.0]})
    pl.load_dataframe(df, "with_nulls", engine, schema=TEST_SCHEMA)
    back = pd.read_sql(text(f'SELECT * FROM "{TEST_SCHEMA}".with_nulls ORDER BY id'), engine)
    assert back["val"].isna().sum() == 1


def test_replace_is_idempotent(engine):
    df = pd.DataFrame({"id": [1, 2]})
    pl.load_dataframe(df, "idem", engine, schema=TEST_SCHEMA)
    pl.load_dataframe(df, "idem", engine, schema=TEST_SCHEMA)
    assert _count(engine, "idem") == 2  # replaced, not appended


def test_load_all_reports_rowcounts(engine):
    dataframes = {
        "t_a": pd.DataFrame({"x": range(5)}),
        "t_b": pd.DataFrame({"y": range(8)}),
    }
    report = pl.load_all(dataframes, engine=engine, schema=TEST_SCHEMA)
    assert report == {"t_a": 5, "t_b": 8}
    assert _count(engine, "t_a") == 5
    assert _count(engine, "t_b") == 8


@pytest.mark.parametrize("csv_path", sorted(glob.glob("data/*_dim.csv")))
def test_dimension_csvs_load_with_matching_rowcounts(engine, csv_path):
    name = os.path.splitext(os.path.basename(csv_path))[0]
    df = pd.read_csv(csv_path)
    rows = pl.load_dataframe(df, name, engine, schema=TEST_SCHEMA)
    assert rows == len(df)
    assert _count(engine, name) == len(df)
