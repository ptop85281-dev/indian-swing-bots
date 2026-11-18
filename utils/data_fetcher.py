import yfinance as yf
import pandas as pd

def get_stock_data(symbol: str, period: str = "3mo"):
    """
    NSE સ્ટોકનો ડેટા લાવે છે
    symbol ઉદાહરણ: RELIANCE.NS, TCS.NS, INFY.NS
    """
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def get_nifty_data(period: str = "3mo"):
    return get_stock_data("^NSEI", period)
