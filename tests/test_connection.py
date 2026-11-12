
import logging
import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


def test_connection() -> None:
    """Test the connection to SQL Server using environment variables."""

    # Load environment variables from the project root
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    # Read database configuration
    server = os.getenv("DB_SERVER")
    driver = os.getenv("DB_DRIVER")
    trusted_connection = os.getenv("DB_TRUSTED_CONNECTION", "yes")
    encrypt = os.getenv("DB_ENCRYPT", "yes")
    trust_certificate = os.getenv(
        "DB_TRUST_SERVER_CERTIFICATE", "no"
    )

    if not server or not driver:
        logger.error("Database server or driver configuration is missing.")
        return

    # Connect to master because EcommerceDB has not been created yet
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        "DATABASE=master;"
        f"Trusted_Connection={trusted_connection};"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust_certificate};"
    )

    try:
        with pyodbc.connect(connection_string, timeout=10) as connection:
            cursor = connection.cursor()

            cursor.execute("SELECT @@SERVERNAME, DB_NAME()")
            result = cursor.fetchone()

            logger.info("Successfully connected to SQL Server.")
            logger.info("Server: %s", result[0])
            logger.info("Database: %s", result[1])

    except pyodbc.Error:
        logger.exception("SQL Server connection failed.")


if __name__ == "__main__":
    test_connection()
