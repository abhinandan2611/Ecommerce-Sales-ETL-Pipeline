import pandas as pd
from pathlib import Path
from scripts.transform import generate_quality_report
from scripts.transform import clean_data
from scripts.transform import transform_data
from scripts.transform import transform_file
from scripts.transform import investigate_missing_values
from scripts.transform import investigate_relationships
from scripts.transform import main


def test_clean_data_removes_duplicates():
    # Arrange: Create a DataFrame with duplicate records
    data = {
        "order_id": [1001, 1002, 1002],
        "product_name": ["Laptop", "Mouse", "Mouse"],
        "quantity": [1, 2, 2]
    }

    df = pd.DataFrame(data)

    # Act: Run the transformation function
    result = clean_data(df)

    # Assert: Check whether duplicates were removed
    assert len(result) == 2
    assert result["order_id"].is_unique

def test_clean_data_standardizes_text():
    # Arrange
    data = {
        "order_id": [1001, 1002],
        "product_name": [" Laptop ", " Mouse "],
        "order_status": [" shipped ", "DELIVERED"],
        "payment_method": [" credit card ", "PAYPAL"]
    }

    df = pd.DataFrame(data)

    # Act
    result = clean_data(df)

    # Assert
    assert result["product_name"].tolist() == ["Laptop", "Mouse"]
    assert result["order_status"].tolist() == ["Shipped", "Delivered"]
    assert result["payment_method"].tolist() == ["Credit Card", "Paypal"]


def test_generate_quality_report(tmp_path):
    """Check whether the quality report is generated correctly."""

    # Arrange
    df = pd.DataFrame({
        "order_id": [1001, 1002, 1002, 1003],
        "quantity": [2, -1, -1, 1],
        "unit_price": [50.0, -10.0, -10.0, 25.0],
        "customer_id": [2001, None, None, 2004]
    })

    output_folder = tmp_path / "reports"

    # Act
    generate_quality_report(
        df=df,
        output_folder=output_folder,
        file_name="test_sales"
    )

    # Assert
    report_path = output_folder / "test_sales_quality_report.csv"

    assert report_path.exists()

    report = pd.read_csv(report_path)

    assert "Issue" in report.columns
    assert "Column" in report.columns
    assert "Affected Records" in report.columns
    assert "Percentage" in report.columns

    assert report.loc[
    report["Issue"] == "Missing Values",
    "Affected Records"
    ].iloc[0] == 2

    assert report.loc[
        report["Issue"] == "Duplicate Records",
        "Affected Records"
    ].iloc[0] == 1

    assert report.loc[
        report["Issue"] == "Negative Quantity",
        "Affected Records"
    ].iloc[0] == 2

    assert report.loc[
        report["Issue"] == "Negative Unit Price",
        "Affected Records"
    ].iloc[0] == 2

    assert report.loc[
        report["Issue"] == "Zero Unit Price",
        "Affected Records"
    ].iloc[0] == 0

def test_transform_data_saves_processed_file_and_quality_report(tmp_path):
    """Check whether transform_data cleans and saves the dataset."""

    # Arrange
    df = pd.DataFrame({
        "order_id": [1001, 1002, 1002],
        "customer_id": [2001, 2002, 2002],
        "product_id": [101, 102, 102],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-02"],
        "product_category": ["Electronics", "Clothing", "Clothing"],
        "product_name": ["Laptop", "Shirt", "Shirt"],
        "quantity": [2, 1, 1],
        "unit_price": [500.0, 25.0, 25.0],
        "discount": [0.1, 0.0, 0.0],
        "shipping_cost": [10.0, 5.0, 5.0],
        "region": ["North", "South", "South"],
        "country": ["Germany", "Germany", "Germany"],
        "payment_method": ["Card", "PayPal", "PayPal"],
        "order_status": ["completed", "shipped", "shipped"]
    })

    output_folder = tmp_path / "processed"

    # Act
    cleaned_df = transform_data(
        df=df,
        output_folder=output_folder,
        file_name="sample_sales.csv"
    )

    # Assert
    processed_file = output_folder / "sample_sales.csv"
    quality_report = output_folder / "sample_sales_quality_report.csv"

    assert processed_file.exists()
    assert quality_report.exists()

    assert len(cleaned_df) == 2
    assert len(pd.read_csv(processed_file)) == 2

    assert df.shape[0] == 3  # Original DataFrame remains unchanged

def test_transform_file(tmp_path):
    """Check whether transform_file reads and processes a CSV file."""

    # Arrange
    raw_folder = tmp_path / "raw"
    output_folder = tmp_path / "processed"

    raw_folder.mkdir()

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
        "order_status": ["completed", "shipped"]
    })

    input_file = raw_folder / "sample_sales.csv"
    df.to_csv(input_file, index=False)

    # Act
    transform_file(input_file, output_folder)

    # Assert
    processed_file = output_folder / "sample_sales.csv"
    quality_report = output_folder / "sample_sales_quality_report.csv"

    assert processed_file.exists()
    assert quality_report.exists()

    processed_df = pd.read_csv(processed_file)

    assert len(processed_df) == 2
    assert list(processed_df.columns) == list(df.columns)

def test_investigate_missing_values(capsys):
    """Check whether missing values are correctly reported."""

    # Arrange
    df = pd.DataFrame({
        "customer_id": [101, None, 103, None],
        "unit_price": [50.0, 25.0, None, 75.0],
        "region": ["North", "South", "East", "West"]
    })

    # Act
    investigate_missing_values(df)

    captured = capsys.readouterr()

    # Assert
    assert "Missing Value Investigation" in captured.out
    assert "customer_id" in captured.out
    assert "unit_price" in captured.out
    assert "Missing Count" in captured.out

def test_investigate_relationships(capsys):
    """Check whether relationship investigations run successfully."""

    # Arrange
    df = pd.DataFrame({
        "order_id": [1001, 1002, 1003],
        "product_id": [101, 102, 101],
        "product_name": ["Laptop", "Shirt", "Laptop"],
        "quantity": [2, -1, 1],
        "unit_price": [500.0, -25.0, 450.0],
        "country": ["Germany", "Germany", "France"],
        "region": ["North", "South", "West"],
        "order_status": ["Completed", "Cancelled", "Shipped"]
    })

    # Act
    investigate_relationships(df)

    captured = capsys.readouterr()

    # Assert
    assert "Product price investigation" in captured.out
    assert "Negative price records" in captured.out
    assert "Negative quantity records" in captured.out
    assert "Product name and price investigation" in captured.out
    assert "Country and region investigation" in captured.out
    assert "Order status of invalid records" in captured.out

def test_main_processes_csv_files(monkeypatch, tmp_path):
    """Check whether main discovers and processes CSV files."""

    # Arrange
    raw_folder = tmp_path / "data" / "raw"
    output_folder = tmp_path / "data" / "processed"

    raw_folder.mkdir(parents=True)

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
        "order_status": ["completed"]
    })

    input_file = raw_folder / "sample_sales.csv"
    df.to_csv(input_file, index=False)

    monkeypatch.setattr(
        "scripts.transform.get_project_root",
        lambda: tmp_path
    )

    # Act
    main()

    # Assert
    processed_file = output_folder / "sample_sales.csv"
    quality_report = output_folder / "sample_sales_quality_report.csv"

    assert processed_file.exists()
    assert quality_report.exists()