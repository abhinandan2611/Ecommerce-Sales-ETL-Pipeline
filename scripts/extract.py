
"""Extract and combine incoming e-commerce sales CSV files."""

import logging
from pathlib import Path

import pandas as pd

from scripts.explore_data import get_project_root, discover_csv_files

logger = logging.getLogger(__name__)


def extract_data() -> tuple[pd.DataFrame, list[Path]]:
    """
    Discover and combine all incoming CSV files.

    Returns:
        A tuple containing the combined DataFrame and source file paths.
    """

    project_root = get_project_root()
    raw_folder = project_root / "data" / "raw"

    csv_files = discover_csv_files(raw_folder)

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {raw_folder}"
        )

    dataframes = []
    expected_columns = None

    for file_path in csv_files:

        logger.info("Extracting data from: %s", file_path.name)

        df = pd.read_csv(file_path)

        # Check that all files have the same columns
        if expected_columns is None:
            expected_columns = list(df.columns)

        elif list(df.columns) != expected_columns:
            raise ValueError(
                f"Incompatible columns found in {file_path.name}. "
                "All incoming CSV files must have the same columns."
            )

        dataframes.append(df)

        logger.info(
            "Extracted %s records from %s",
            len(df),
            file_path.name
        )

    # Combine all extracted datasets
    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    logger.info("Batch extraction completed successfully.")
    logger.info("Files extracted: %s", len(csv_files))
    logger.info("Total extracted records: %s", len(combined_df))

    return combined_df, csv_files
