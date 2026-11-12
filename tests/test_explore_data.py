
from pathlib import Path

import pandas as pd
import pytest

import scripts.explore_data as explore


def test_get_project_root(monkeypatch, tmp_path):
    """Check whether the project root is identified correctly."""

    fake_file = tmp_path / "scripts" / "explore_data.py"
    monkeypatch.setattr(explore, "__file__", str(fake_file))

    result = explore.get_project_root()

    assert result == tmp_path


def test_discover_csv_files(tmp_path):
    """Check whether CSV files are discovered."""

    (tmp_path / "sales.csv").touch()
    (tmp_path / "customers.csv").touch()
    (tmp_path / "notes.txt").touch()

    result = explore.discover_csv_files(tmp_path)

    assert len(result) == 2
    assert all(file.suffix == ".csv" for file in result)


def test_discover_csv_files_when_folder_is_empty(tmp_path, caplog):
    """Check warning when no CSV files are found."""

    result = explore.discover_csv_files(tmp_path)

    assert result == []
    assert "No CSV files found" in caplog.text


def test_explore_csv_file_successfully(tmp_path, capsys):
    """Check whether CSV dataset information is displayed."""

    file_path = tmp_path / "sales.csv"

    df = pd.DataFrame({
        "order_id": [101, 102, 103],
        "quantity": [2, 3, 1],
        "unit_price": [10.5, 20.0, 15.0]
    })

    df.to_csv(file_path, index=False)

    explore.explore_csv_file(file_path)

    output = capsys.readouterr().out

    assert "DATASET: sales.csv" in output
    assert "Rows: 3" in output
    assert "Columns: 3" in output
    assert "order_id" in output
    assert "First five records" in output
    assert "Data types" in output
    assert "Basic statistical summary" in output


@pytest.mark.parametrize(
    "error",
    [
        pd.errors.ParserError("Invalid CSV"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid byte"),
        OSError("File cannot be accessed")
    ]
)
def test_explore_csv_file_handles_read_errors(
    tmp_path, monkeypatch, caplog, error
):
    """Check whether CSV reading errors are handled."""

    file_path = tmp_path / "invalid.csv"
    file_path.touch()

    def raise_error(*args, **kwargs):
        raise error

    monkeypatch.setattr(pd, "read_csv", raise_error)

    explore.explore_csv_file(file_path)

    assert "Could not read invalid.csv" in caplog.text


def test_main_when_csv_files_are_found(monkeypatch, tmp_path):
    """Check whether main explores all discovered CSV files."""

    csv_files = [
        tmp_path / "sales.csv",
        tmp_path / "customers.csv"
    ]

    explored_files = []

    monkeypatch.setattr(
        explore,
        "get_project_root",
        lambda: tmp_path
    )

    monkeypatch.setattr(
        explore,
        "discover_csv_files",
        lambda folder: csv_files
    )

    monkeypatch.setattr(
        explore,
        "explore_csv_file",
        lambda file_path: explored_files.append(file_path)
    )

    explore.main()

    assert explored_files == csv_files


def test_main_when_no_csv_files_are_found(monkeypatch, tmp_path):
    """Check whether main exits when no CSV files are found."""

    monkeypatch.setattr(
        explore,
        "get_project_root",
        lambda: tmp_path
    )

    monkeypatch.setattr(
        explore,
        "discover_csv_files",
        lambda folder: []
    )

    def unexpected_call(file_path):
        pytest.fail("explore_csv_file should not be called")

    monkeypatch.setattr(
        explore,
        "explore_csv_file",
        unexpected_call
    )

    explore.main()
