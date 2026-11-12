
"""Explore raw CSV datasets using Pandas."""

import logging 
from pathlib import Path

import pandas as pd


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Return the root directory of the ETL project."""
    return Path(__file__).resolve().parent.parent


def discover_csv_files(raw_folder: Path) -> list[Path]:
    """Find all CSV files in the raw data folder."""
    csv_files = list(raw_folder.glob("*.csv"))

    if not csv_files:
        logger.warning("No CSV files found in %s", raw_folder)

    return csv_files


def explore_csv_file(file_path: Path) -> None:
    """Display an initial overview of a CSV dataset."""

    logger.info("Exploring file: %s", file_path.name)

    try:
        df = pd.read_csv(file_path)

        print("\n" + "=" * 50)
        print(f"DATASET: {file_path.name}")
        print("=" * 50)

        print("\n1. Dataset dimensions:")
        print(f"Rows: {df.shape[0]}")
        print(f"Columns: {df.shape[1]}")

        print("\n2. Column names:")
        print(df.columns.tolist())

        print("\n3. First five records:")
        print(df.head())

        print("\n4. Data types:")
        print(df.dtypes)

        print("\n5. Dataset information:")
        df.info()

        print("\n6. Basic statistical summary:")
        print(df.describe(include="all"))

    except (pd.errors.ParserError, UnicodeDecodeError, OSError) as error:
        logger.exception("Could not read %s: %s", file_path.name, error)


def main() -> None:
    """Run the initial exploration of all raw CSV datasets."""

    project_root = get_project_root()
    raw_folder = project_root / "data" / "raw"

    csv_files = discover_csv_files(raw_folder)

    if not csv_files:
        return

    for file_path in csv_files:
        explore_csv_file(file_path)


if __name__ == "__main__":
    main()
