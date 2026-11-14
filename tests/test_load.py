
import pandas as pd
import pytest
import scripts.load as load
from pathlib import Path

from scripts.load import prepare_dataframe
from unittest.mock import MagicMock
from scripts.load import get_project_root
from scripts.load import create_db_engine
from scripts.load import load_data



def test_prepare_dataframe_converts_dates_and_integers():
    """Check date and integer column conversions."""

    # Arrange
    df = pd.DataFrame({
        "order_id": [1001, 1002],
        "customer_id": [2001, 2002],
        "product_id": [3001, 3002],
        "order_date": ["2026-01-15", "15/02/2026"],
        "quantity": [2, 3]
    })

    # Act
    result = prepare_dataframe(df)

    # Assert
    assert result["order_date"].tolist() == [
        pd.Timestamp("2026-01-15").date(),
        pd.Timestamp("2026-02-15").date()
    ]

    integer_columns = [
        "order_id",
        "customer_id",
        "product_id",
        "quantity"
    ]

    for column in integer_columns:
        assert str(result[column].dtype) == "Int64"


def test_prepare_dataframe_does_not_modify_original():
    """Check that the original DataFrame remains unchanged."""

    # Arrange
    df = pd.DataFrame({
        "order_id": [1001],
        "customer_id": [2001],
        "product_id": [3001],
        "order_date": ["2026-01-15"],
        "quantity": [2]
    })

    original_df = df.copy(deep=True)

    # Act
    prepare_dataframe(df)

    # Assert
    pd.testing.assert_frame_equal(df, original_df)


def test_load_data_loads_only_new_records(monkeypatch):
    """Check that existing order IDs are skipped during loading."""

    # Arrange: incoming records
    valid_df = pd.DataFrame({
        "order_id": [1001, 1003],
        "customer_id": [2001, 2003],
        "product_id": [3001, 3003],
        "order_date": ["2026-01-15", "2026-01-17"],
        "quantity": [2, 3]
    })

    quarantine_df = pd.DataFrame({
        "order_id": [1002, 1004],
        "customer_id": [2002, 2004],
        "product_id": [3002, 3004],
        "order_date": ["2026-01-16", "2026-01-18"],
        "quantity": [-1, -2],
        "quarantine_reason": [
            "Negative quantity",
            "Negative quantity"
        ]
    })

    mock_engine = MagicMock()
    mock_connection = MagicMock()

    mock_engine.begin.return_value.__enter__.return_value = mock_connection

    # Simulate IDs already present in the database
    mock_connection.execute.return_value.fetchall.return_value = [
        (1001,),
        (1002,)
    ]

    monkeypatch.setattr(
        load,
        "create_db_engine",
        lambda: mock_engine
    )

    loaded_dataframes = []

    def mock_to_sql(self, *args, **kwargs):
        loaded_dataframes.append(self.copy())

    monkeypatch.setattr(pd.DataFrame, "to_sql", mock_to_sql)

        # Act
    load.load_data(valid_df, quarantine_df)

    # Assert: only new records should be loaded
    assert len(loaded_dataframes) == 2

    loaded_valid = loaded_dataframes[0]
    loaded_quarantine = loaded_dataframes[1]

    assert loaded_valid["order_id"].tolist() == [1003]
    assert loaded_quarantine["order_id"].tolist() == [1004]

    # No DELETE statements should be executed
    executed_sql = str(mock_connection.execute.call_args.args[0])
    assert "DELETE" not in executed_sql.upper()

    mock_engine.dispose.assert_called_once()


def test_load_data_disposes_engine_when_loading_fails(monkeypatch):
    """Engine should be disposed even when database loading fails."""

    # Arrange
    valid_df = pd.DataFrame({
        "order_id": [1001],
        "customer_id": [2001],
        "product_id": [3001],
        "order_date": ["2026-01-15"],
        "quantity": [2]
    })

    quarantine_df = pd.DataFrame({
        "order_id": [1002],
        "customer_id": [2002],
        "product_id": [3002],
        "order_date": ["2026-01-16"],
        "quantity": [-1],
        "quarantine_reason": ["Negative quantity"]
    })

    mock_engine = MagicMock()
    mock_connection = MagicMock()

    mock_engine.begin.return_value.__enter__.return_value = (
        mock_connection
    )

    monkeypatch.setattr(
        load,
        "create_db_engine",
        lambda: mock_engine
    )

    def simulate_database_failure(*args, **kwargs):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(
        pd.DataFrame,
        "to_sql",
        simulate_database_failure
    )

    # Act and Assert
    import pytest

    with pytest.raises(
        RuntimeError,
        match="Simulated database failure"
    ):
        load.load_data(valid_df, quarantine_df)

    mock_engine.dispose.assert_called_once()


def test_load_data_handles_transaction_failure(monkeypatch):
    """Check transaction handling when quarantine loading fails."""

    import pytest

    # Arrange
    valid_df = pd.DataFrame({
        "order_id": [1001],
        "customer_id": [2001],
        "product_id": [3001],
        "order_date": ["2026-01-15"],
        "quantity": [2]
    })

    quarantine_df = pd.DataFrame({
        "order_id": [1002],
        "customer_id": [2002],
        "product_id": [3002],
        "order_date": ["2026-01-16"],
        "quantity": [-1],
        "quarantine_reason": ["Negative quantity"]
    })

    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_transaction = MagicMock()

    mock_transaction.__enter__.return_value = mock_connection
    mock_engine.begin.return_value = mock_transaction

    monkeypatch.setattr(
        load,
        "create_db_engine",
        lambda: mock_engine
    )

    call_count = 0

    def simulate_failure_on_second_load(self, *args, **kwargs):
        nonlocal call_count
        call_count += 1

        if call_count == 2:
            raise RuntimeError("Quarantine loading failed")

    monkeypatch.setattr(
        pd.DataFrame,
        "to_sql",
        simulate_failure_on_second_load
    )

    # Act and Assert
    with pytest.raises(
        RuntimeError,
        match="Quarantine loading failed"
    ):
        load.load_data(valid_df, quarantine_df)

    # Verify both loading attempts occurred
    assert call_count == 2

    # Verify the transaction received the exception
    assert mock_transaction.__exit__.call_args[0][0] is RuntimeError

    # Verify the engine was disposed
    mock_engine.dispose.assert_called_once()

def test_get_project_root():
    """Check whether the project root directory is returned correctly."""

    project_root = get_project_root()

    expected_root = Path(__file__).resolve().parent.parent

    assert project_root == expected_root
    assert project_root.name == "ETL_Project"

def test_create_db_engine_missing_configuration(monkeypatch):
    """Check whether missing database configuration raises an error."""

    from scripts.load import create_db_engine

    monkeypatch.setattr(
        "scripts.load.load_dotenv",
        lambda *args, **kwargs: None
    )

    monkeypatch.delenv("DB_SERVER", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_DRIVER", raising=False)

    with pytest.raises(
        ValueError,
        match="Missing database configuration"
    ):
        create_db_engine()

def test_create_db_engine_successfully(monkeypatch):
    """Check whether the database engine is created with valid configuration."""

    monkeypatch.setattr(
        "scripts.load.load_dotenv",
        lambda *args, **kwargs: None
    )

    monkeypatch.setenv("DB_SERVER", "TEST_SERVER")
    monkeypatch.setenv("DB_NAME", "TEST_DATABASE")
    monkeypatch.setenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    monkeypatch.setenv("DB_TRUSTED_CONNECTION", "yes")
    monkeypatch.setenv("DB_ENCRYPT", "yes")
    monkeypatch.setenv("DB_TRUST_SERVER_CERTIFICATE", "yes")

    mock_engine = MagicMock()

    mock_create_engine = MagicMock(return_value=mock_engine)

    monkeypatch.setattr(
        "scripts.load.create_engine",
        mock_create_engine
    )

    result = create_db_engine()

    assert result is mock_engine

    mock_create_engine.assert_called_once()

    _, kwargs = mock_create_engine.call_args

    assert kwargs["fast_executemany"] is True
    assert kwargs["pool_pre_ping"] is True

def test_create_db_engine_uses_default_settings(monkeypatch):
    """Check whether default database settings are applied."""

    monkeypatch.setattr(
        "scripts.load.load_dotenv",
        lambda *args, **kwargs: None
    )

    monkeypatch.setenv("DB_SERVER", "TEST_SERVER")
    monkeypatch.setenv("DB_NAME", "TEST_DATABASE")
    monkeypatch.setenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

    monkeypatch.delenv("DB_TRUSTED_CONNECTION", raising=False)
    monkeypatch.delenv("DB_ENCRYPT", raising=False)
    monkeypatch.delenv("DB_TRUST_SERVER_CERTIFICATE", raising=False)

    mock_engine = MagicMock()
    mock_create_engine = MagicMock(return_value=mock_engine)

    monkeypatch.setattr(
        "scripts.load.create_engine",
        mock_create_engine
    )

    result = create_db_engine()

    assert result is mock_engine

    connection_url = mock_create_engine.call_args.args[0]

    connection_string = connection_url.query["odbc_connect"]

    assert "Trusted_Connection=yes" in connection_string
    assert "Encrypt=yes" in connection_string
    assert "TrustServerCertificate=no" in connection_string

def test_prepare_dataframe_handles_missing_integer_values():
    """Check whether nullable integer columns preserve missing values."""

    df = pd.DataFrame({
        "order_id": [1001, 1002],
        "customer_id": [2001, None],
        "product_id": [101, 102],
        "quantity": [2, 3],
        "order_date": ["2026-01-01", "2026-01-02"],
        "unit_price": [50.0, 75.0]
    })

    result = prepare_dataframe(df)

    assert str(result["customer_id"].dtype) == "Int64"
    assert pd.isna(result.loc[1, "customer_id"])
    assert result.loc[0, "customer_id"] == 2001

def test_prepare_dataframe_handles_mixed_date_formats():
    """Check whether different date formats are converted correctly."""

    df = pd.DataFrame({
        "order_id": [1001, 1002],
        "customer_id": [2001, 2002],
        "product_id": [101, 102],
        "quantity": [2, 3],
        "order_date": ["2026-01-01", "02/01/2026"],
        "unit_price": [50.0, 75.0]
    })

    result = prepare_dataframe(df)

    assert result["order_date"].iloc[0] == pd.Timestamp("2026-01-01").date()
    assert result["order_date"].iloc[1] == pd.Timestamp("2026-02-01").date()

def test_prepare_dataframe_rejects_invalid_dates():
    """Check whether invalid dates raise an error."""

    df = pd.DataFrame({
        "order_id": [1001],
        "customer_id": [2001],
        "product_id": [101],
        "quantity": [2],
        "order_date": ["not-a-date"],
        "unit_price": [50.0]
    })

    with pytest.raises(ValueError):
        prepare_dataframe(df)


def test_load_data_when_engine_creation_fails(monkeypatch):
    """Check whether database engine creation errors are propagated."""

    valid_df = pd.DataFrame({
        "order_date": ["2026-01-01"],
        "order_id": [1001],
        "customer_id": [2001],
        "product_id": [101],
        "quantity": [2]
    })

    quarantine_df = valid_df.copy()

    def raise_connection_error():
        raise RuntimeError("Database connection failed")

    monkeypatch.setattr(
        "scripts.load.create_db_engine",
        raise_connection_error
    )

    with pytest.raises(RuntimeError, match="Database connection failed"):
        load_data(valid_df, quarantine_df)


    def raise_connection_error():
        raise RuntimeError("Database connection failed")

    monkeypatch.setattr(
        "scripts.load.create_db_engine",
        raise_connection_error
    )

    with pytest.raises(
        RuntimeError,
        match="Database connection failed"
    ):
        load_data(valid_df, quarantine_df)


def test_load_data_removes_duplicate_ids_within_incoming_data(monkeypatch):
    """Check that duplicate incoming order IDs are inserted only once."""

    valid_df = pd.DataFrame({
        "order_id": [1001, 1001, 1002],
        "customer_id": [2001, 2001, 2002],
        "product_id": [3001, 3001, 3002],
        "order_date": ["2026-01-15", "2026-01-15", "2026-01-16"],
        "quantity": [2, 2, 3]
    })

    quarantine_df = pd.DataFrame(columns=[
        "order_id",
        "customer_id",
        "product_id",
        "order_date",
        "quantity"
    ])

    mock_engine = MagicMock()
    mock_connection = MagicMock()

    mock_engine.begin.return_value.__enter__.return_value = mock_connection
    mock_connection.execute.return_value.fetchall.return_value = []

    monkeypatch.setattr(
        load,
        "create_db_engine",
        lambda: mock_engine
    )

    loaded_dataframes = []

    def mock_to_sql(self, *args, **kwargs):
        loaded_dataframes.append(self.copy())

    monkeypatch.setattr(pd.DataFrame, "to_sql", mock_to_sql)

    load.load_data(valid_df, quarantine_df)

    assert len(loaded_dataframes) == 1
    assert loaded_dataframes[0]["order_id"].tolist() == [1001, 1002]

    mock_engine.dispose.assert_called_once()
