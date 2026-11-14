
"""Main entry point for the batch e-commerce ETL pipeline."""

import logging
import shutil
import time

from scripts.extract import extract_data
from scripts.transform import transform_data
from scripts.validate import validate_data
from scripts.load import load_data
from scripts.logging_config import configure_logging
from scripts.explore_data import get_project_root


logger = logging.getLogger(__name__)


def archive_source_files(source_files, archive_folder):
    """Move successfully processed source files into the archive."""

    archive_folder.mkdir(parents=True, exist_ok=True)

    for source_file in source_files:

        destination = archive_folder / source_file.name

        # Avoid overwriting an existing archived file
        counter = 1

        while destination.exists():
            destination = archive_folder / (
                f"{source_file.stem}_{counter}{source_file.suffix}"
            )
            counter += 1

        shutil.move(str(source_file), str(destination))

        logger.info("Archived source file: %s", destination.name)


def main() -> None:
    """Execute the complete batch ETL pipeline."""

    configure_logging()
    start_time = time.perf_counter()

    try:
        logger.info("Starting batch e-commerce ETL pipeline.")

        project_root = get_project_root()

        processed_folder = project_root / "data" / "processed"
        archive_folder = processed_folder / "source_files"

        # Step 1: Extract all incoming CSV files
        raw_df, source_files = extract_data()

        logger.info("Files received: %s", len(source_files))
        logger.info("Total incoming records: %s", len(raw_df))

        # Step 2: Transform the combined dataset
        transformed_df = transform_data(
            df=raw_df,
            output_folder=processed_folder,
            file_name="batch_processed.csv"
        )

        # Step 3: Validate and separate records
        valid_df, quarantine_df = validate_data(
            df=transformed_df,
            output_folder=processed_folder
        )

        # Step 4: Incrementally load records into SQL Server
        load_data(
            valid_df=valid_df,
            quarantine_df=quarantine_df
        )

        # Step 5: Archive source files only after successful loading
        archive_source_files(
            source_files=source_files,
            archive_folder=archive_folder
        )

        logger.info("Batch ETL pipeline completed successfully.")

    except Exception:
        logger.exception("Batch ETL pipeline failed.")
        raise

    finally:
        execution_time = time.perf_counter() - start_time

        logger.info(
            "Total pipeline execution time: %.2f seconds",
            execution_time
        )


if __name__ == "__main__":
    main()
