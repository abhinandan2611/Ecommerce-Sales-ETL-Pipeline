
"""Validate the processed e-commerce sales dataset."""

import logging
from pathlib import Path

import pandas as pd

from scripts.explore_data import get_project_root, discover_csv_files


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


def validate_columns(df: pd.DataFrame) -> bool:
    """Check whether all required columns are present."""

    required_columns = [
        "order_id",
        "customer_id",
        "product_id",
        "order_date",
        "product_category",
        "product_name",
        "quantity",
        "unit_price",
        "discount",
        "shipping_cost",
        "region",
        "country",
        "payment_method",
        "order_status"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        logger.error("Missing columns: %s", missing_columns)
        return False

    logger.info("Column validation passed.")
    return True


def validate_duplicates(df: pd.DataFrame) -> bool:
    """Check whether exact duplicate records exist."""

    duplicate_count = df.duplicated().sum()

    if duplicate_count > 0:
        logger.error("Found %s duplicate records.", duplicate_count)
        return False

    logger.info("Duplicate validation passed.")
    return True


def validate_numeric_values(df: pd.DataFrame) -> bool:
    """Check numeric columns for invalid values."""

    checks = {
        "quantity": df["quantity"] < 0,
        "unit_price": df["unit_price"] <= 0,
        "shipping_cost": df["shipping_cost"] < 0,
        "discount": (df["discount"] < 0) | (df["discount"] > 1)
    }

    valid = True

    for column, condition in checks.items():
        invalid_count = condition.sum()

        if invalid_count > 0:
            logger.error(
                "%s contains %s invalid values.",
                column,
                invalid_count
            )
            valid = False

    if valid:
        logger.info("Numeric validation passed.")

    return valid


def validate_missing_values(df: pd.DataFrame) -> bool:
    """Check required columns for missing values."""

    required_fields = [
        "order_id",
        "product_id",
        "order_date",
        "quantity",
        "unit_price"
    ]

    missing_counts = df[required_fields].isna().sum()

    invalid_fields = missing_counts[missing_counts > 0]

    if not invalid_fields.empty:
        logger.error(
            "Missing values found in required fields:\n%s",
            invalid_fields
        )
        return False

    logger.info("Missing-value validation passed.")
    return True



def validate_data_types(df: pd.DataFrame) -> bool:
    """Check whether columns have appropriate data types."""

    expected_types = {
        "order_id": "integer",
        "product_id": "integer",
        "quantity": "integer",
        "unit_price": "numeric",
        "discount": "numeric",
        "shipping_cost": "numeric"
    }

    valid = True

    for column, expected_type in expected_types.items():

        actual_type = df[column].dtype

        if expected_type == "integer":
            is_valid = pd.api.types.is_integer_dtype(actual_type)

        elif expected_type == "numeric":
            is_valid = pd.api.types.is_numeric_dtype(actual_type)

        if not is_valid:
            logger.error(
                "%s has an unexpected data type: %s",
                column,
                actual_type
            )
            valid = False

    if valid:
        logger.info("Data type validation passed.")

    return valid



def validate_dates(df: pd.DataFrame) -> bool:
    """Check whether order_date contains valid dates."""

    dates = pd.to_datetime(
        df["order_date"],
        errors="coerce",
        format="mixed"
    )

    invalid_count = dates.isna().sum()

    if invalid_count > 0:
        logger.error(
            "Found %s missing or invalid order dates.",
            invalid_count
        )
        return False

    logger.info("Date validation passed.")
    return True



def separate_valid_invalid(
    df: pd.DataFrame,
    output_folder: Path
) -> None:
    """Separate valid records from records requiring investigation."""

    # Identify records that violate our business rules
    invalid_mask = (
        df["unit_price"].isna()
        | (df["unit_price"] <= 0)
        | (df["quantity"] < 0)
        | (df["shipping_cost"] < 0)
        | (df["discount"] < 0)
        | (df["discount"] > 1)
    )

    valid_records = df.loc[~invalid_mask].copy()
    quarantined_records = df.loc[invalid_mask].copy()

    # Add reasons for quarantine
    quarantined_records["quarantine_reason"] = ""

    conditions = {
        "Missing unit price": df["unit_price"].isna(),
        "Invalid unit price": df["unit_price"] <= 0,
        "Negative quantity": df["quantity"] < 0,
        "Negative shipping cost": df["shipping_cost"] < 0,
        "Invalid discount": (df["discount"] < 0) | (df["discount"] > 1)
    }

    
    for reason, condition in conditions.items():

        matching_indices = df.index[condition & invalid_mask]

        quarantined_records.loc[
            matching_indices, "quarantine_reason"
        ] += reason + "; "


    output_folder.mkdir(parents=True, exist_ok=True)

    valid_records.to_csv(
        output_folder / "valid_records.csv",
        index=False
    )

    quarantined_records.to_csv(
        output_folder / "quarantined_records.csv",
        index=False
    )

    logger.info("Valid records: %s", len(valid_records))
    logger.info("Quarantined records: %s", len(quarantined_records))



def validate_data(
    df: pd.DataFrame,
    output_folder: Path
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate a DataFrame, separate invalid records and return both datasets."""

    logger.info("Starting data validation.")

    # Check the structure before applying business rules.
    structural_checks = [
        validate_columns(df),
        validate_duplicates(df),
        validate_data_types(df),
        validate_dates(df)
    ]

    if not all(structural_checks):
        raise ValueError(
            "Structural validation failed. Cannot continue."
        )

    # Separate records based on current quarantine rules.
    separate_valid_invalid(df, output_folder)

    # Read the separated datasets for subsequent validation.
    valid_file = output_folder / "valid_records.csv"
    quarantine_file = output_folder / "quarantined_records.csv"

    valid_records = pd.read_csv(valid_file)
    quarantined_records = pd.read_csv(quarantine_file)

    # Validate records eligible for loading.
    final_checks = [
        validate_missing_values(valid_records),
        validate_numeric_values(valid_records)
    ]

    if not all(final_checks):
        raise ValueError(
            "Validation failed for records marked as valid."
        )

    logger.info("Data validation completed successfully.")
    logger.info("Valid records: %s", len(valid_records))
    logger.info("Quarantined records: %s", len(quarantined_records))

    return valid_records, quarantined_records


def validate_file(file_path: Path) -> None:
    """Run validation checks on a processed CSV file."""

    logger.info("Validating file: %s", file_path.name)

    df = pd.read_csv(file_path)

    print("\nDiscount values:")
    print(sorted(df["discount"].dropna().unique()))

    print("\nShipping cost summary:")
    print(df["shipping_cost"].describe())

    results = [
        validate_columns(df),
        validate_duplicates(df),
        validate_missing_values(df),
        validate_data_types(df),
        validate_dates(df)
    ]

    # Run numeric checks only when required columns exist
    if all(
        column in df.columns
        for column in ["quantity", "unit_price", "shipping_cost", "discount"]
    ):
        results.append(validate_numeric_values(df))

    if all(results):
        logger.info("All validation checks passed.")
    else:
        logger.warning("Validation failed. Review the errors above.")



def main() -> None:
    """Validate the processed sales dataset independently."""

    project_root = get_project_root()
    processed_folder = project_root / "data" / "processed"

    csv_files = [
        file_path
        for file_path in discover_csv_files(processed_folder)
        if file_path.name == "ecommerce_sales_1000_records.csv"
    ]

    if not csv_files:
        logger.error(
            "No processed sales CSV file found in: %s",
            processed_folder
        )
        return

    for file_path in csv_files:
        logger.info("Validating file: %s", file_path.name)

        try:
            df = pd.read_csv(file_path)
            validate_data(df, processed_folder)

        except Exception:
            logger.exception(
                "Failed to validate file: %s",
                file_path.name
            )


if __name__ == "__main__":
    main()

