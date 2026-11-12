
import logging
from pathlib import Path

import pandas as pd

from scripts.explore_data import get_project_root, discover_csv_files


logger = logging.getLogger(__name__)


def extract_data() -> tuple[pd.DataFrame, Path]:
    """
    Discover and extract the raw CSV dataset.

    Returns:
        A tuple containing the extracted DataFrame and source file path.
    """

    project_root = get_project_root()
    raw_folder = project_root / "data" / "raw"

    csv_files = discover_csv_files(raw_folder)

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {raw_folder}"
        )

    if len(csv_files) > 1:
        raise ValueError(
            f"Expected one raw CSV file, but found {len(csv_files)}."
        )

    file_path = csv_files[0]

    logger.info("Extracting data from: %s", file_path.name)

    df = pd.read_csv(file_path)

    logger.info("Extraction completed successfully.")
    logger.info("Extracted records: %s", len(df))
    logger.info("Extracted columns: %s", len(df.columns))

    return df, file_path
