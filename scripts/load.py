
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


def load_data(
    valid_df: pd.DataFrame,
    quarantine_df: pd.DataFrame
) -> None:
    """Load valid and quarantined records into SQL Server."""

    # Prepare both datasets before changing database contents.
    valid_df = prepare_dataframe(valid_df)
    quarantine_df = prepare_dataframe(quarantine_df)

    engine = create_db_engine()

    try:
        # Load both datasets within one transaction.
        with engine.begin() as connection:

            # Remove previous records for a full refresh.
            connection.execute(
                text("DELETE FROM dbo.sales_orders")
            )

            connection.execute(
                text("DELETE FROM dbo.quarantined_sales_orders")
            )

            # Load valid records.
            valid_df.to_sql(
                name="sales_orders",
                schema="dbo",
                con=connection,
                if_exists="append",
                index=False,
                chunksize=500
            )

            # Load quarantined records.
            quarantine_df.to_sql(
                name="quarantined_sales_orders",
                schema="dbo",
                con=connection,
                if_exists="append",
                index=False,
                chunksize=500
            )

        logger.info("Data loading completed successfully.")
        logger.info("Valid records loaded: %s", len(valid_df))
        logger.info("Quarantined records loaded: %s", len(quarantine_df))

    finally:
        engine.dispose()


if __name__ == "__main__":
    logger.info(
        "Run the complete pipeline through main.py to load data."
    )
