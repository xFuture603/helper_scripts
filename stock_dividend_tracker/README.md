# Dividend Payout Dates Tool

This script retrieves the latest dividend payout dates for a list of stocks using the Yahoo Finance API. It provides information on the last dividend payout date and predicts future dividend payouts based on Ex-Dividend Dates where available.

<table border=1 cellpadding=10><tr><td>

#### \*\*\* IMPORTANT LEGAL DISCLAIMER \*\*\*

---

**Yahoo!, Y!Finance, and Yahoo! finance are registered trademarks of
Yahoo, Inc.**

This script is **not** affiliated, endorsed, or vetted by Yahoo, Inc. It's
an open-source tool that uses Yahoo's publicly available APIs, and is
intended for research and educational purposes.

**You should refer to Yahoo!'s terms of use**
([here](https://policies.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.htm),
[here](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html), and
[here](https://policies.yahoo.com/us/en/yahoo/terms/index.htm)) **for
details on your rights to use the actual data downloaded. Remember - the
Yahoo! finance API is intended for personal use only.**

</td></tr></table>

## Use Cases

You can use this script to quickly check when a stock last paid dividends and when it is expected to pay dividends in the future. It's useful for investors and analysts who monitor dividend income from their investments. You also can use this script to generate an output for a Telegram bot like I do.

## Requirements

- Python 3
- `yfinance` library
- `pytz` library
- `argparse` library

You can install the required libraries using:

```sh
pip3 install -r requirements.txt
```

## Usage

The script can be run from the command line. It supports both a YAML configuration file and direct input of stock tickers as command-line arguments.

### Running with a Configuration File:

```sh
python3 stock_dividend_tracker.py --config config.yml
```

**Example Configuration File (config.yaml)**:

```yaml
stocks:
  - AAPL
  - MSFT
  - GME
  - FLXS
  - DIS
```

### Running with Direct Stock Tickers:

```sh
python3 stock_dividend_tracker.py AAPL MSFT GOOGL
```

## Arguments

- `--config` (optional): Path to a YAML configuration file containing a list of stock tickers.
- Positional arguments: List of stock tickers to fetch dividend payout dates for.

## Example Output

When the script is run, it prints the dividend payout information formatted as follows:

```md
AAPL: Dividends are in the past, last payout was on 2024-05-10.
No future Ex-Dividend Date found.

MSFT: Dividends are in the past, last payout was on 2024-05-15.
Next Ex-Dividend Date: 2024-08-15

GME: Dividends are in the past, last payout was on 2019-03-14.
No future Ex-Dividend Date found.

FLXS: Dividends are in the past, last payout was on 2024-06-26.
No future Ex-Dividend Date found.

DIS: Dividends are in the past, last payout was on 2023-12-08.
Next Ex-Dividend Date: 2024-07-05
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
