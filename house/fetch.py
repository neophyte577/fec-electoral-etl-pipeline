from pathlib import Path
from decimal import Decimal
import os
import time

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import snowflake.connector
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

QUERY_PATH = Path(__file__).with_name("pull_house.sql")
OUTPUT_PATH = Path(__file__).with_name("house_model_base.parquet")

INT_COLS = {"CYCLE", "DISTRICT", "OUTCOME"}
BOOL_COLS = {"UNOPPOSED"}
DATE_COLS = {"CVG_END_DT", "FIRST_INDIV_TXN_DT", "LAST_INDIV_TXN_DT"}


def get_connection():
    print("ACCOUNT =", os.environ.get("SNOWFLAKE_ACCOUNT"))
    print("USER    =", os.environ.get("SNOWFLAKE_USER"))
    print("WH      =", os.environ.get("SNOWFLAKE_WAREHOUSE"))
    print("DB      =", os.environ.get("SNOWFLAKE_DATABASE"))
    print("SCHEMA  =", os.environ.get("SNOWFLAKE_SCHEMA"))
    print("ROLE    =", os.environ.get("SNOWFLAKE_ROLE"))

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PAT"],
        role=os.environ.get("SNOWFLAKE_ROLE"),
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ.get("SNOWFLAKE_DATABASE", "FEC"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "RAW"),
    )


def looks_decimal(series: pd.Series) -> bool:
    sample = series.dropna().head(20)
    return not sample.empty and sample.map(lambda x: isinstance(x, Decimal)).any()


def normalize_batch(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in df.columns:
        s = df[col]

        if col in BOOL_COLS:
            df[col] = s.astype("boolean")
        elif col in DATE_COLS:
            df[col] = pd.to_datetime(s, errors="coerce")
        elif col in INT_COLS:
            df[col] = pd.to_numeric(s, errors="coerce").astype("Int64")
        elif pd.api.types.is_numeric_dtype(s) or looks_decimal(s):
            df[col] = pd.to_numeric(s, errors="coerce").astype("float64")
        else:
            df[col] = s.astype("string")

    return df


def strip_metadata(table: pa.Table) -> pa.Table:
    clean_schema = table.schema.remove_metadata()
    return pa.Table.from_arrays(table.columns, schema=clean_schema)


def main():
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()

    print("Loading SQL...")
    sql = QUERY_PATH.read_text(encoding="utf-8")

    print("Connecting to Snowflake...")
    t0 = time.time()
    conn = get_connection()
    print(f"Connected in {time.time() - t0:.1f}s")

    writer = None
    target_schema = None
    total_rows = 0

    try:
        with conn.cursor() as cur:
            print("Submitting query...")
            t1 = time.time()
            cur.execute(sql)
            print(f"Query submitted in {time.time() - t1:.1f}s")

            print("Fetching batches...")
            for i, batch in enumerate(cur.fetch_pandas_batches(), start=1):
                if batch.empty:
                    print(f"Batch {i} was empty")
                    continue

                batch = normalize_batch(batch)

                table = pa.Table.from_pandas(batch, preserve_index=False)
                table = strip_metadata(table)

                if target_schema is None:
                    target_schema = table.schema
                    writer = pq.ParquetWriter(
                        OUTPUT_PATH,
                        target_schema,
                        compression="snappy",
                    )
                else:
                    table = table.cast(target_schema, safe=False)

                writer.write_table(table)
                total_rows += len(batch)
                print(f"Wrote batch {i} with {len(batch):,} rows")

    finally:
        conn.close()
        if writer is not None:
            writer.close()

    print(f"All done: {total_rows:,} rows written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()