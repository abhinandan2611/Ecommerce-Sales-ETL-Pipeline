
import pandas as pd
import pytest

import scripts.extract as extract


def test_extract_data_successfully(monkeypatch, tmp_path):
    """A single CSV file should be extracted successfully."""

    raw_folder = tmp_path / "data" / "raw"
    raw_folder.mkdir(parents=True)

    csv_file = raw_folder / "test_sales.csv"

    expected_df = pd.DataFrame({
        "order_id": [1001, 1002],
        "quantity": [2, 3]
    })

    expected_df.to_csv(csv_file, index=False)

    monkeypatch.setattr(
        extract,
        "get_project_root",
        lambda: tmp_path
    )

    result_df, source_files = extract.extract_data()

    pd.testing.assert_frame_equal(result_df, expected_df)
    assert source_files == [csv_file]


def test_extract_data_file_not_found(monkeypatch, tmp_path):
    """Extraction should fail when no CSV file exists."""

    raw_folder = tmp_path / "data" / "raw"
    raw_folder.mkdir(parents=True)

    monkeypatch.setattr(
        extract,
        "get_project_root",
        lambda: tmp_path
    )

    with pytest.raises(FileNotFoundError):
        extract.extract_data()


def test_extract_data_multiple_files(monkeypatch, tmp_path):
    """Multiple CSV files should be combined into one DataFrame."""

    raw_folder = tmp_path / "data" / "raw"
    raw_folder.mkdir(parents=True)

    df1 = pd.DataFrame({
        "order_id": [1001, 1002],
        "quantity": [2, 3]
    })

    df2 = pd.DataFrame({
        "order_id": [1003, 1004],
        "quantity": [4, 5]
    })

    file1 = raw_folder / "sales1.csv"
    file2 = raw_folder / "sales2.csv"

    df1.to_csv(file1, index=False)
    df2.to_csv(file2, index=False)

    monkeypatch.setattr(
        extract,
        "get_project_root",
        lambda: tmp_path
    )

    result_df, source_files = extract.extract_data()

    expected_df = pd.concat(
        [df1, df2],
        ignore_index=True
    )

    pd.testing.assert_frame_equal(result_df, expected_df)

    assert source_files == [file1, file2]


def test_extract_data_rejects_incompatible_columns(monkeypatch, tmp_path):
    """Files with different columns should raise an error."""

    raw_folder = tmp_path / "data" / "raw"
    raw_folder.mkdir(parents=True)

    pd.DataFrame({
        "order_id": [1001],
        "quantity": [2]
    }).to_csv(raw_folder / "sales1.csv", index=False)

    pd.DataFrame({
        "order_id": [1002],
        "unit_price": [50.0]
    }).to_csv(raw_folder / "sales2.csv", index=False)

    monkeypatch.setattr(
        extract,
        "get_project_root",
        lambda: tmp_path
    )

    with pytest.raises(ValueError, match="columns"):
        extract.extract_data()
