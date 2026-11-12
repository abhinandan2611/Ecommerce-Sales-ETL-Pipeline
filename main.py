
"""Main entry point for the e-commerce ETL pipeline."""

import logging
import time

from scripts.extract import extract_data
from scripts.transform import transform_data
from scripts.validate import validate_data
from scripts.load import load_data
from scripts.logging_config import configure_logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Execute the complete e-commerce ETL pipeline."""

    configure_logging()
    start_time = time.perf_counter()

    try:
        logger.info("Starting e-commerce ETL pipeline.")

        # Step 1: Extract
        raw_df, source_file = extract_data()

        # Step 2: Transform
        from scripts.explore_data import get_project_root

        project_root = get_project_root()
        processed_folder = project_root / "data" / "processed"

        transformed_df = transform_data(
            df=raw_df,
            output_folder=processed_folder,
            file_name=source_file.name
        )

        # Step 3: Validate and separate records
        valid_df, quarantine_df = validate_data(
            df=transformed_df,
            output_folder=processed_folder
        )

        # Step 4: Load into SQL Server
        load_data(
            valid_df=valid_df,
            quarantine_df=quarantine_df
        )

        logger.info("ETL pipeline completed successfully.")

        

    except Exception:
        logger.exception("ETL pipeline failed.")
        raise
    
    finally:
        end_time = time.perf_counter()
        execution_time = end_time - start_time

        logger.info(
            "Total pipeline execution time: %.2f seconds",
            execution_time
        )


if __name__ == "__main__":
    main()
