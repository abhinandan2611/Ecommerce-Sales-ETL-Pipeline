
"""Transform raw e-commerce sales data."""

import logging
from pathlib import Path

import pandas as pd

from scripts.explore_data import get_project_root, discover_csv_files


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicates and standardise text fields."""

    # Remove exact duplicate records
    df = df.drop_duplicates().copy()

    # Remove leading and trailing spaces from text columns
    text_columns = df.select_dtypes(include=["object", "string"]).columns

    for column in text_columns:
        df[column] = df[column].str.strip()

    # Standardise selected text columns
    for column in ["order_status", "payment_method"]:
        if column in df.columns:
            df[column] = df[column].str.title()

    return df


def investigate_missing_values(df: pd.DataFrame) -> None:
    """Display missing-value counts and percentages."""

    missing_count = df.isna().sum()

    missing_percentage = (
        df.isna().mean() * 100
    ).round(2)

    missing_summary = pd.DataFrame({
        "Missing Count": missing_count,
        "Missing Percentage": missing_percentage
    })

    missing_summary = missing_summary[
        missing_summary["Missing Count"] > 0
    ]

    print("\nMissing Value Investigation:")
    print(missing_summary)


def investigate_relationships(df: pd.DataFrame) -> None:
    """Check whether other columns can help recover missing values."""

    print("\nProduct price investigation:")

    price_check = (
        df.groupby("product_id")["unit_price"]
        .agg(["count", "nunique", "mean", "min", "max"])
    )

    print(price_check.head(10))

    print("\nNegative price records:")
    print(df[df["unit_price"] < 0][
        ["order_id", "product_id", "product_name", "quantity", "unit_price"]
    ])

    print("\nNegative quantity records:")
    print(df[df["quantity"] < 0][
        ["order_id", "product_id", "product_name", "quantity", "unit_price"]
    ])

    print("\nProduct name and price investigation:")

    name_price_check = (
    df.groupby("product_name")["unit_price"]
    .agg(["count", "nunique", "mean", "min", "max"])
   ) 
    print(name_price_check.head(10))


    print("\nCountry and region investigation:")

    region_check = (
        df.groupby("country")["region"]
        .nunique()
    )

    print(region_check)

    print("\nCountries with multiple regions:")
    print(region_check[region_check > 1])

    print("\nNegative price records:")
    print(df[df["unit_price"] < 0][
        ["order_id", "product_id", "product_name", "quantity", "unit_price"]
    ])

    print("\nNegative quantity records:")
    print(df[df["quantity"] < 0][
        ["order_id", "product_id", "product_name", "quantity", "unit_price"]
    ])

    print("\nOrder status of invalid records:")

    invalid_records = df[
        (df["unit_price"] < 0) |
        (df["quantity"] < 0)
    ]

    print(
        invalid_records[
            ["order_id", "product_name", "quantity",
            "unit_price", "order_status"]
        ]
)


def generate_quality_report(
    df: pd.DataFrame,
    output_folder: Path,
    file_name: str
) -> None:
    """Generate a summary report of data quality issues."""

    total_rows = len(df)

    report = []

    # Check missing values in each column
    for column in df.columns:
        missing_count = df[column].isna().sum()

        if missing_count > 0:
            report.append({
                "Issue": "Missing Values",
                "Column": column,
                "Affected Records": missing_count,
                "Percentage": round(missing_count / total_rows * 100, 2)
            })

    # Check duplicate records
    duplicate_count = df.duplicated().sum()

    report.append({
        "Issue": "Duplicate Records",
        "Column": "All Columns",
        "Affected Records": duplicate_count,
        "Percentage": round(duplicate_count / total_rows * 100, 2)
    })

    # Check negative and zero values
    checks = {
        "Negative Quantity": df["quantity"] < 0,
        "Negative Unit Price": df["unit_price"] < 0,
        "Zero Unit Price": df["unit_price"] == 0
    }

    for issue, condition in checks.items():
        affected_count = condition.sum()

        report.append({
            "Issue": issue,
            "Column": "quantity" if "Quantity" in issue else "unit_price",
            "Affected Records": affected_count,
            "Percentage": round(affected_count / total_rows * 100, 2)
        })

    # Convert report into a DataFrame
    quality_report = pd.DataFrame(report)

    # Save report
    output_folder.mkdir(parents=True, exist_ok=True)

    report_path = output_folder / f"{file_name}_quality_report.csv"

    quality_report.to_csv(report_path, index=False)

    logger.info("Data quality report saved to: %s", report_path)



def transform_data(
    df: pd.DataFrame,
    output_folder: Path,
    file_name: str
) -> pd.DataFrame:
    """Transform extracted data and save the processed dataset."""

    # Generate quality report before cleaning
    generate_quality_report(df, output_folder, Path(file_name).stem)

    # Investigate missing values
    investigate_missing_values(df)

    # Investigate relationships between columns
    investigate_relationships(df)

    original_rows = len(df)

    # Clean the extracted DataFrame
    cleaned_df = clean_data(df)

    removed_rows = original_rows - len(cleaned_df)

    # Save processed data
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / file_name
    cleaned_df.to_csv(output_path, index=False)

    logger.info("Processed: %s", file_name)
    logger.info("Original rows: %s", original_rows)
    logger.info("Rows removed: %s", removed_rows)
    logger.info("Final rows: %s", len(cleaned_df))
    logger.info("Saved to: %s", output_path)

    return cleaned_df


def transform_file(file_path: Path, output_folder: Path) -> None:
    """Read and transform a CSV file independently."""

    df = pd.read_csv(file_path)

    transform_data(
        df=df,
        output_folder=output_folder,
        file_name=file_path.name
    )



def main() -> None:
    """Run transformations on all raw CSV files."""

    project_root = get_project_root()

    raw_folder = project_root / "data" / "raw"
    output_folder = project_root / "data" / "processed"

    csv_files = discover_csv_files(raw_folder)

    for file_path in csv_files:
        transform_file(file_path, output_folder)


if __name__ == "__main__":
    main()
