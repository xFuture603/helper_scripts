"""Tests for the stock_dividend_tracker script."""
from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd
import pytest
import pytz
import yaml

from stock_dividend_tracker.stock_dividend_tracker import (
    get_dividend_payout_dates,
    load_config,
    main,
)


@pytest.fixture
def mock_yfinance():
    """Fixture to mock yfinance.Ticker."""
    with patch("yfinance.Ticker") as mock_ticker:
        yield mock_ticker


class MockTicker:
    """A mock class for yfinance.Ticker."""

    def __init__(self, dividends=None, calendar=None, error=None):
        """Initialize the MockTicker."""
        if error:
            raise error
        self.dividends = dividends if dividends is not None else pd.DataFrame()
        self.calendar = calendar if calendar is not None else {}


def test_load_config(tmp_path):
    """Test the load_config function."""
    config_data = {"stocks": ["AAPL", "MSFT"]}
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
    assert load_config(config_file) == config_data


def test_get_dividend_payout_dates_future(mock_yfinance):
    """Test get_dividend_payout_dates with a future ex-dividend date."""
    mock_yfinance.return_value = MockTicker(
        dividends=pd.DataFrame(
            {"Dividends": [0.25]},
            index=[pd.to_datetime("2025-08-15").tz_localize("UTC")],
        ),
        calendar={
            "Ex-Dividend Date": datetime.now(pytz.utc).date() + timedelta(days=10)
        },
    )
    dates = get_dividend_payout_dates(["AAPL"])
    assert "Next Ex-Dividend Date" in dates["AAPL"]


def test_get_dividend_payout_dates_past(mock_yfinance):
    """Test get_dividend_payout_dates with a past ex-dividend date."""
    mock_yfinance.return_value = MockTicker(
        dividends=pd.DataFrame(
            {"Dividends": [0.25]},
            index=[pd.to_datetime("2024-01-01").tz_localize("UTC")],
        ),
        calendar={"Ex-Dividend Date": datetime(2024, 1, 1).date()},
    )
    dates = get_dividend_payout_dates(["AAPL"])
    assert "Dividends are in the past" in dates["AAPL"]


def test_get_dividend_payout_dates_no_dividends(mock_yfinance):
    """Test get_dividend_payout_dates with no dividend information."""
    mock_yfinance.return_value = MockTicker()
    dates = get_dividend_payout_dates(["GOOG"])
    assert dates["GOOG"] == "No dividends found."


def test_get_dividend_payout_dates_error(mock_yfinance):
    """Test get_dividend_payout_dates with an error."""
    mock_yfinance.side_effect = Exception("Test error")
    dates = get_dividend_payout_dates(["FAIL"])
    assert "Error: Test error" in dates["FAIL"]


@patch("argparse.ArgumentParser")
@patch("stock_dividend_tracker.stock_dividend_tracker.load_config")
def test_main_with_config(mock_load_config, mock_argparse, tmp_path):
    """Test the main function with a config file."""
    mock_load_config.return_value = {"stocks": ["AAPL"]}
    config_file = tmp_path / "config.yaml"

    mock_args = mock_argparse.return_value.parse_args.return_value
    mock_args.config = str(config_file)
    mock_args.stocks = []

    with patch(
        "stock_dividend_tracker.stock_dividend_tracker.get_dividend_payout_dates"
    ) as mock_get_dates:
        main()
        mock_get_dates.assert_called_once_with(["AAPL"])


@patch("argparse.ArgumentParser")
def test_main_with_args(mock_argparse):
    """Test the main function with command-line arguments."""
    mock_args = mock_argparse.return_value.parse_args.return_value
    mock_args.config = None
    mock_args.stocks = ["MSFT"]

    with patch(
        "stock_dividend_tracker.stock_dividend_tracker.get_dividend_payout_dates"
    ) as mock_get_dates:
        main()
        mock_get_dates.assert_called_once_with(["MSFT"])


@patch("argparse.ArgumentParser")
def test_main_no_stocks(mock_argparse, capsys):
    """Test the main function with no stocks provided."""
    mock_args = mock_argparse.return_value.parse_args.return_value
    mock_args.config = None
    mock_args.stocks = []

    main()
    captured = capsys.readouterr()
    assert "No stocks provided." in captured.out
