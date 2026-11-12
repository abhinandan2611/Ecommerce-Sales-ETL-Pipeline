
import pandas as pd
import pytest

import scripts.extract as extract


def test_extract_data_successfully(monkeypatch, tmp_path):
    """A single CSV file should be extracted successfully."""

    # Arrange
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

    # Act
    result_df, source_file = extract.extract_data()

    # Assert
    pd.testing.assert_frame_equal(result_df, expected_df)
    assert source_file == csv_file


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
    """Extraction should fail when multiple CSV files exist."""

    raw_folder = tmp_path / "data" / "raw"
    raw_folder.mkdir(parents=True)

    (raw_folder / "sales1.csv").touch()
    (raw_folder / "sales2.csv").touch()

    monkeypatch.setattr(
        extract,
        "get_project_root",
        lambda: tmp_path
    )

    with pytest.raises(ValueError):
        extract.extract_data()
