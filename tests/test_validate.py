
import pandas as pd
import pytest
import logging

from scripts.validate import (
    validate_dates,
    validate_numeric_values,
    validate_missing_values
)
from scripts.validate import validate_columns
from scripts.validate import validate_duplicates
from scripts.validate import validate_data_types
from scripts.validate import separate_valid_invalid
from scripts.validate import validate_data
from scripts.validate import validate_file
from scripts.validate import main



def test_numeric_validation_passes():
    """Valid numerical values should pass validation."""

    df = pd.DataFrame({
        "quantity": [1, 2, 3],
        "unit_price": [10.50, 25.00, 30.00],
        "shipping_cost": [2.50, 3.00, 0.00],
        "discount": [0.0, 0.10, 1.0]
    })

    assert validate_numeric_values(df) is True


def test_numeric_validation_fails():
    """Invalid numerical values should fail validation."""

    df = pd.DataFrame({
        "quantity": [1, -2],
        "unit_price": [10.50, -5.00],
        "shipping_cost": [2.50, -3.00],
        "discount": [0.10, 1.50]
    })

    assert validate_numeric_values(df) is False


def test_missing_value_validation_passes():
    """Complete required fields should pass validation."""

    df = pd.DataFrame({
        "order_id": [1001, 1002],
        "product_id": [3001, 3002],
        "order_date": ["2026-01-01", "2026-01-02"],
        "quantity": [1, 2],
        "unit_price": [10.50, 25.00]
    })

    assert validate_missing_values(df) is True


def test_missing_value_validation_fails():
    """Missing required values should fail validation."""

    df = pd.DataFrame({
        "order_id": [1001, None],
        "product_id": [3001, 3002],
        "order_date": ["2026-01-01", "2026-01-02"],
        "quantity": [1, 2],
        "unit_price": [10.50, None]
    })

    assert validate_missing_values(df) is False


def test_date_validation_passes():
    """Valid date formats should pass validation."""

    from scripts.validate import validate_dates

    df = pd.DataFrame({
        "order_date": [
            "2026-01-15",
            "15/02/2026",
            "March 10, 2026"
        ]
    })

    assert validate_dates(df) is True


def test_date_validation_fails():
    """Invalid or missing dates should fail validation."""

    from scripts.validate import validate_dates

    df = pd.DataFrame({
        "order_date": [
            "2026-01-15",
            "invalid-date",
            None
        ]
    })

    assert validate_dates(df) is False

def test_validate_columns_passes():
    """Check whether all required columns are present."""

    df = pd.DataFrame({
        "order_id": [1001],
        "customer_id": [2001],
        "product_id": [101],
        "order_date": ["2026-01-01"],
        "product_category": ["Electronics"],
        "product_name": ["Laptop"],
        "quantity": [2],
        "unit_price": [500.0],
        "discount": [0.1],
        "shipping_cost": [10.0],
        "region": ["North"],
        "country": ["Germany"],
        "payment_method": ["Card"],
        "order_status": ["Completed"]
    })

    result = validate_columns(df)

    assert result is True

def test_validate_columns_fails():
    """Check whether missing required columns are detected."""

    df = pd.DataFrame({
        "order_id": [1001],
        "customer_id": [2001],
        "product_id": [101]
    })

    result = validate_columns(df)

    assert result is False

def test_validate_duplicates_passes():
    """Check whether a dataset without duplicates passes."""

    df = pd.DataFrame({
        "order_id": [1001, 1002, 1003],
        "product_id": [101, 102, 103]
    })

    result = validate_duplicates(df)

    assert result is True

def test_validate_duplicates_fails():
    """Check whether duplicate records are detected."""

    df = pd.DataFrame({
        "order_id": [1001, 1002, 1002],
        "product_id": [101, 102, 102]
    })

    result = validate_duplicates(df)

    assert result is False

def test_validate_data_types_passes():
    """Check whether correct data types pass validation."""

    df = pd.DataFrame({
        "order_id": [1001, 1002],
        "product_id": [101, 102],
        "quantity": [2, 3],
        "unit_price": [50.0, 75.0],
        "discount": [0.1, 0.2],
        "shipping_cost": [5.0, 10.0]
    })

    result = validate_data_types(df)

    assert result is True

def test_validate_data_types_fails():
    """Check whether incorrect data types are detected."""

    df = pd.DataFrame({
        "order_id": ["ABC", "XYZ"],
        "product_id": [101, 102],
        "quantity": [2, 3],
        "unit_price": [50.0, 75.0],
        "discount": [0.1, 0.2],
        "shipping_cost": [5.0, 10.0]
    })

    result = validate_data_types(df)

    assert result is False

def test_validate_dates_mixed_formats():
    """Check whether different valid date formats are accepted."""

    df = pd.DataFrame({
        "order_date": [
            "2026-01-01",
            "02/01/2026",
            "January 3, 2026"
        ]
    })

    result = validate_dates(df)

    assert result is True

def test_validate_dates_invalid_value():
    """Check whether invalid dates are detected."""

    df = pd.DataFrame({
        "order_date": [
            "2026-01-01",
            "not-a-date",
            "2026-01-03"
        ]
    })

    result = validate_dates(df)

    assert result is False

def test_separate_valid_invalid(tmp_path):
    """Check whether valid and invalid records are separated."""

    # Arrange
    df = pd.DataFrame({
        "order_id": [1001, 1002, 1003],
        "customer_id": [2001, 2002, 2003],
        "product_id": [101, 102, 103],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "quantity": [2, -1, 3],
        "unit_price": [50.0, 25.0, -10.0],
        "discount": [0.1, 0.2, 0.0],
        "shipping_cost": [5.0, 10.0, 5.0]
    })

    # Act
    valid_df, invalid_df = separate_valid_invalid(df, tmp_path)

    # Assert
    assert len(valid_df) == 1
    assert len(invalid_df) == 2

    assert "quarantine_reason" in invalid_df.columns

    assert (tmp_path / "valid_records.csv").exists()
    assert (tmp_path / "quarantined_records.csv").exists()

def test_validate_data_returns_valid_and_invalid_records(tmp_path):
    """Check whether the main validation function returns both datasets."""

    df = pd.DataFrame({
        "order_id": [1001, 1002, 1003],
        "customer_id": [2001, 2002, 2003],
        "product_id": [101, 102, 103],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "product_category": ["Electronics", "Clothing", "Electronics"],
        "product_name": ["Laptop", "Shirt", "Phone"],
        "quantity": [2, -1, 3],
        "unit_price": [50.0, 25.0, -10.0],
        "discount": [0.1, 0.2, 0.0],
        "shipping_cost": [5.0, 10.0, 5.0],
        "region": ["North", "South", "East"],
        "country": ["Germany", "Germany", "France"],
        "payment_method": ["Card", "PayPal", "Card"],
        "order_status": ["Completed", "Cancelled", "Shipped"]
    })

    valid_df, invalid_df = validate_data(df, tmp_path)

    assert len(valid_df) == 1
    assert len(invalid_df) == 2

    assert "quarantine_reason" in invalid_df.columns

    assert (tmp_path / "valid_records.csv").exists()
    assert (tmp_path / "quarantined_records.csv").exists()

def test_validate_data_fails_on_duplicates(tmp_path):
    """Check whether structural validation stops when duplicates exist."""

    # Arrange
    df = pd.DataFrame({
        "order_id": [1001, 1001],
        "customer_id": [2001, 2001],
        "product_id": [101, 101],
        "order_date": ["2026-01-01", "2026-01-01"],
        "product_category": ["Electronics", "Electronics"],
        "product_name": ["Laptop", "Laptop"],
        "quantity": [2, 2],
        "unit_price": [500.0, 500.0],
        "discount": [0.1, 0.1],
        "shipping_cost": [10.0, 10.0],
        "region": ["North", "North"],
        "country": ["Germany", "Germany"],
        "payment_method": ["Card", "Card"],
        "order_status": ["Completed", "Completed"]
    })

    # Act and Assert
    with pytest.raises(
        ValueError,
        match="Structural validation failed"
    ):
        validate_data(df, tmp_path)

def test_validate_data_fails_on_final_validation(
    monkeypatch, tmp_path
):
    """Check whether final validation failures raise an error."""

    df = pd.DataFrame({
        "order_id": [1001],
        "customer_id": [2001],
        "product_id": [101],
        "order_date": ["2026-01-01"],
        "product_category": ["Electronics"],
        "product_name": ["Laptop"],
        "quantity": [2],
        "unit_price": [500.0],
        "discount": [0.1],
        "shipping_cost": [10.0],
        "region": ["North"],
        "country": ["Germany"],
        "payment_method": ["Card"],
        "order_status": ["Completed"]
    })

    monkeypatch.setattr(
        "scripts.validate.validate_numeric_values",
        lambda df: False
    )

    with pytest.raises(
        ValueError,
        match="Validation failed for records marked as valid"
    ):
        validate_data(df, tmp_path)

def test_validate_file_successfully(tmp_path, caplog):
    """Check whether a valid CSV file is processed successfully."""

    # Arrange
    df = pd.DataFrame({
        "order_id": [1001, 1002],
        "customer_id": [2001, 2002],
        "product_id": [101, 102],
        "order_date": ["2026-01-01", "2026-01-02"],
        "product_category": ["Electronics", "Clothing"],
        "product_name": ["Laptop", "Shirt"],
        "quantity": [2, 1],
        "unit_price": [500.0, 25.0],
        "discount": [0.1, 0.0],
        "shipping_cost": [10.0, 5.0],
        "region": ["North", "South"],
        "country": ["Germany", "Germany"],
        "payment_method": ["Card", "PayPal"],
        "order_status": ["Completed", "Shipped"]
    })

    file_path = tmp_path / "sample_sales.csv"
    df.to_csv(file_path, index=False)

    # Act
    with caplog.at_level(logging.INFO):
        validate_file(file_path)

    # Assert
    assert "All validation checks passed." in caplog.text

def test_validate_file_with_invalid_data(tmp_path, caplog):
    """Check whether invalid CSV data produces a validation warning."""

    df = pd.DataFrame({
        "order_id": [1001, 1002],
        "customer_id": [2001, 2002],
        "product_id": [101, 102],
        "order_date": ["2026-01-01", "2026-01-02"],
        "product_category": ["Electronics", "Clothing"],
        "product_name": ["Laptop", "Shirt"],
        "quantity": [2, -1],
        "unit_price": [500.0, 25.0],
        "discount": [0.1, 0.0],
        "shipping_cost": [10.0, 5.0],
        "region": ["North", "South"],
        "country": ["Germany", "Germany"],
        "payment_method": ["Card", "PayPal"],
        "order_status": ["Completed", "Shipped"]
    })

    file_path = tmp_path / "invalid_sales.csv"
    df.to_csv(file_path, index=False)

    with caplog.at_level(logging.WARNING):
        validate_file(file_path)

    assert "Validation failed. Review the errors above." in caplog.text

def test_main_validates_processed_file(monkeypatch, tmp_path, caplog):
    """Check whether main discovers and validates the processed CSV."""

    processed_folder = tmp_path / "data" / "processed"
    processed_folder.mkdir(parents=True)

    df = pd.DataFrame({
        "order_id": [1001],
        "customer_id": [2001],
        "product_id": [101],
        "order_date": ["2026-01-01"],
        "product_category": ["Electronics"],
        "product_name": ["Laptop"],
        "quantity": [2],
        "unit_price": [500.0],
        "discount": [0.1],
        "shipping_cost": [10.0],
        "region": ["North"],
        "country": ["Germany"],
        "payment_method": ["Card"],
        "order_status": ["Completed"]
    })

    file_path = processed_folder / "ecommerce_sales_1000_records.csv"
    df.to_csv(file_path, index=False)

    monkeypatch.setattr(
        "scripts.validate.get_project_root",
        lambda: tmp_path
    )

    with caplog.at_level(logging.INFO):
        main()

    assert "Data validation completed successfully." in caplog.text

def test_main_when_processed_file_is_missing(
    monkeypatch, tmp_path, caplog
):
    """Check whether main handles a missing processed CSV."""

    processed_folder = tmp_path / "data" / "processed"
    processed_folder.mkdir(parents=True)

    monkeypatch.setattr(
        "scripts.validate.get_project_root",
        lambda: tmp_path
    )

    with caplog.at_level(logging.ERROR):
        main()

    assert "No processed sales CSV file found" in caplog.text