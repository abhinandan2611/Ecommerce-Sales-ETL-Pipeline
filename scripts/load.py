
"""Load validated e-commerce sales data into SQL Server."""

import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


def create_db_engine():
    """Create a SQLAlchemy engine using environment variables."""

    project_root = get_project_root()
    load_dotenv(project_root / ".env")

    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    driver = os.getenv("DB_DRIVER")
    trusted_connection = os.getenv("DB_TRUSTED_CONNECTION", "yes")
    encrypt = os.getenv("DB_ENCRYPT", "yes")
    trust_certificate = os.getenv(
        "DB_TRUST_SERVER_CERTIFICATE", "no"
    )

    if not all([server, database, driver]):
        raise ValueError("Missing database configuration in .env")

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection={trusted_connection};"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust_certificate};"
    )

    connection_url = URL.create(
        "mssql+pyodbc",
        query={"odbc_connect": connection_string}
    )

    return create_engine(
        connection_url,
        fast_executemany=True,
        pool_pre_ping=True
    )


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare a DataFrame for SQL Server loading."""

    df = df.copy()

    # Convert dates into a consistent format.
    df["order_date"] = pd.to_datetime(
        df["order_date"],
        format="mixed",
        errors="raise"
    ).dt.date

    # Convert ID and quantity columns to nullable integers.
    integer_columns = [
        "order_id",
        "customer_id",
        "product_id",
        "quantity"
    ]

    for column in integer_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        ).astype("Int64")

    return df



def load_data(valid_df: pd.DataFrame, quarantine_df: pd.DataFrame) -> None:
    """Load only new order IDs into SQL Server."""

    valid_df = prepare_dataframe(valid_df)
    quarantine_df = prepare_dataframe(quarantine_df)

    engine = create_db_engine()

    try:
        with engine.begin() as connection:

            # Get order IDs already present in either database table
            result = connection.execute(text("""
                SELECT order_id FROM dbo.sales_orders
                UNION
                SELECT order_id FROM dbo.quarantined_sales_orders
            """))

            existing_ids = {
                row[0] for row in result.fetchall()
            }

            # Remove records that already exist in the database
            valid_df = valid_df[
                ~valid_df["order_id"].isin(existing_ids)
            ].copy()

            # Remove duplicate IDs within the incoming valid data
            valid_df = valid_df.drop_duplicates(
                subset=["order_id"],
                keep="first"
            )

            # Include newly accepted valid IDs when filtering quarantine
            existing_ids.update(valid_df["order_id"].dropna().tolist())

            quarantine_df = quarantine_df[
                ~quarantine_df["order_id"].isin(existing_ids)
            ].copy()

            quarantine_df = quarantine_df.drop_duplicates(
                subset=["order_id"],
                keep="first"
            )

            # Insert only new records
            if not valid_df.empty:
                valid_df.to_sql(
                    name="sales_orders",
                    schema="dbo",
                    con=connection,
                    if_exists="append",
                    index=False,
                    chunksize=500
                )

            if not quarantine_df.empty:
                quarantine_df.to_sql(
                    name="quarantined_sales_orders",
                    schema="dbo",
                    con=connection,
                    if_exists="append",
                    index=False,
                    chunksize=500
                )

        logger.info("Incremental data loading completed successfully.")
        logger.info("New valid records loaded: %s", len(valid_df))
        logger.info("New quarantined records loaded: %s", len(quarantine_df))

    finally:
        engine.dispose()


def load_warehouse() -> None:
    """Execute the SQL Server warehouse incremental load procedure."""

    engine = create_db_engine()

    try:
        with engine.connect() as connection:
            try:
                logger.info("Starting data warehouse incremental load.")

                connection.execute(
                    text("EXEC dw.usp_load_warehouse")
                )

                connection.commit()

                logger.info(
                    "Data warehouse incremental load completed successfully."
                )

            except Exception:
                connection.rollback()
                logger.exception(
                    "Data warehouse incremental load failed."
                )
                raise

    finally:
        engine.dispose()



if __name__ == "__main__":
    logger.info(
        "Run the complete pipeline through main.py to load data."
    )
