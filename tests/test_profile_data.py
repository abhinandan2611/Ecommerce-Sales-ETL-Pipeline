
import pandas as pd
import pytest

import scripts.profile_data as profile


def sample_dataframe():
    return pd.DataFrame({
        "order_id": [101, 102, 103, 103],
        "quantity": [2, -1, 3, 3],
        "unit_price": [10.0, 20.0, 0, 15.0],
        "shipping_cost": [5.0, -2.0, 3.0, 3.0],
        "discount": [10, 110, -5, 10]
    })


def test_check_invalid_values(capsys):
    """Check whether invalid numeric values are identified."""

    df = sample_dataframe()

    profile.check_invalid_values(df)

    output = capsys.readouterr().out

    assert "quantity: 1 invalid records" in output
    assert "unit_price: 1 invalid records" in output
    assert "shipping_cost: 1 invalid records" in output
    assert "discount: 2 invalid records" in output


def test_check_invalid_values_with_valid_data(capsys):
    """Check whether valid numeric values produce zero invalid records."""

    df = pd.DataFrame({
        "quantity": [1, 2, 3],
        "unit_price": [10.0, 20.0, 30.0],
        "shipping_cost": [2.0, 3.0, 4.0],
        "discount": [0, 10, 50]
    })

    profile.check_invalid_values(df)

    output = capsys.readouterr().out

    assert "quantity: 0 invalid records" in output
    assert "unit_price: 0 invalid records" in output
    assert "shipping_cost: 0 invalid records" in output
    assert "discount: 0 invalid records" in output


def test_profile_data_successfully(tmp_path, capsys):
    """Check whether dataset profiling displays the correct information."""

    file_path = tmp_path / "sales.csv"

    df = sample_dataframe()

    # Create one exact duplicate
    df.loc[3] = df.loc[2]

    # Introduce one missing value
    df.loc[0, "quantity"] = None
    df.to_csv(file_path, index=False)

    profile.profile_data(file_path)

    output = capsys.readouterr().out

    assert "Dataset: sales.csv" in output
    assert "Total rows: 4" in output
    assert "Missing values by column:" in output
    assert "Duplicate rows: 1" in output
    assert "Invalid values:" in output


def test_main_profiles_all_csv_files(monkeypatch, tmp_path):
    """Check whether main profiles all discovered CSV files."""

    csv_files = [
        tmp_path / "sales.csv",
        tmp_path / "customers.csv"
    ]

    profiled_files = []

    monkeypatch.setattr(
        profile,
        "get_project_root",
        lambda: tmp_path
    )

    monkeypatch.setattr(
        profile,
        "discover_csv_files",
        lambda folder: csv_files
    )

    monkeypatch.setattr(
        profile,
        "profile_data",
        lambda file_path: profiled_files.append(file_path)
    )

    profile.main()

    assert profiled_files == csv_files


def test_main_when_no_csv_files_exist(monkeypatch, tmp_path):
    """Check whether main handles an empty CSV file list."""

    monkeypatch.setattr(
        profile,
        "get_project_root",
        lambda: tmp_path
    )

    monkeypatch.setattr(
        profile,
        "discover_csv_files",
        lambda folder: []
    )

    def unexpected_call(file_path):
        pytest.fail("profile_data should not be called")

    monkeypatch.setattr(
        profile,
        "profile_data",
        unexpected_call
    )

    profile.main()
