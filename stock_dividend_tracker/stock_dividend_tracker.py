import yfinance as yf
import yaml
import argparse
from datetime import datetime, timedelta
import pytz

def load_config(config_file):
    """
    Load the YAML configuration file.

    Parameters:
    config_file (str): The path to the YAML configuration file.

    Returns:
    dict: A dictionary containing the configuration data.
    """
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def get_dividend_payout_dates(stock_list):
    """
    Get the latest dividend payout dates and predict future dividend payouts based on Ex-Dividend Dates for a list of stocks.

    Parameters:
    stock_list (list): A list of stock ticker symbols.

    Returns:
    dict: A dictionary with stock ticker symbols as keys and their latest dividend payout dates or an error message as values.
    """
    payout_dates = {}
    current_date = datetime.now(pytz.utc)

    for stock in stock_list:
        try:
            ticker = yf.Ticker(stock)
            dividends = ticker.dividends

            if not dividends.empty:
                # Get the latest dividend payout date
                latest_payout_date = dividends.index[-1]

                if latest_payout_date < current_date:
                    latest_payout_date_str = latest_payout_date.strftime('%Y-%m-%d')
                    payout_dates[stock] = f"Dividends are in the past, last payout was on {latest_payout_date_str}."
                else:
                    payout_dates[stock] = latest_payout_date.strftime('%Y-%m-%d')

                # Get the next Ex-Dividend Date
                ex_dividend_dates = ticker.calendar['Ex-Dividend Date']
                ex_dividend_dates = ex_dividend_dates[ex_dividend_dates > current_date]  # Filter out past dates

                if not ex_dividend_dates.empty:
                    next_ex_dividend_date = ex_dividend_dates.min().strftime('%Y-%m-%d')
                    payout_dates[stock] += f" Next Ex-Dividend Date: {next_ex_dividend_date}"
                else:
                    payout_dates[stock] += " No future Ex-Dividend Date found."

            else:
                payout_dates[stock] = "No dividends found."

        except Exception as e:
            payout_dates[stock] = f"Error: {str(e)}"

    return payout_dates

def main():
    """
    Main function to parse command-line arguments and get dividend payout dates for stocks.

    It supports both a YAML configuration file and direct stock ticker input via command-line arguments.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Get dividend payout dates for a list of stocks.')
    parser.add_argument('--config', type=str, help='Path to the YAML configuration file.')
    parser.add_argument('stocks', nargs='*', help='List of stock tickers.')

    # Parse arguments
    args = parser.parse_args()

    # Load stocks from config file if provided
    if args.config:
        config = load_config(args.config)
        stocks = config.get('stocks', [])
    else:
        stocks = []

    # Add any stocks provided as positional arguments
    stocks.extend(args.stocks)

    if stocks:
        dividend_payout_dates = get_dividend_payout_dates(stocks)
        for stock, payout_date in dividend_payout_dates.items():
            print(f"{stock}: {payout_date}")
    else:
        print("No stocks provided.")

if __name__ == '__main__':
    main()
