
"""Profile missing values and duplicates in raw CSV files."""

import logging
from pathlib import Path

import pandas as pd

from explore_data import get_project_root, discover_csv_files


logger = logging.getLogger(__name__)


def profile_data(file_path: Path) -> None:
    """Check a CSV dataset for missing values and duplicates."""

    df = pd.read_csv(file_path)

    print(f"\nDataset: {file_path.name}")
    print(f"Total rows: {len(df)}")

    # Check missing values
    print("\nMissing values by column:")
    print(df.isna().sum())

    # Check duplicate rows
    duplicate_count = df.duplicated().sum()
    print(f"\nDuplicate rows: {duplicate_count}")
    
    check_invalid_values(df)


def check_invalid_values(df: pd.DataFrame) -> None:
    """Identify invalid numeric values in the dataset."""

    checks = {
        "quantity": df["quantity"] < 0,
        "unit_price": df["unit_price"] <= 0,
        "shipping_cost": df["shipping_cost"] < 0,
        "discount": (df["discount"] < 0) | (df["discount"] > 100),
    }

    print("\nInvalid values:")

    for column, condition in checks.items():
        print(f"{column}: {condition.sum()} invalid records")



def main() -> None:
    """Profile all CSV files in the raw data folder."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    raw_folder = get_project_root() / "data" / "raw"
    csv_files = discover_csv_files(raw_folder)

    for file_path in csv_files:
        profile_data(file_path)


if __name__ == "__main__":
    main()
