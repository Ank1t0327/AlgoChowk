"""
Data acquisition: NIFTY 50 daily OHLC.

Source: Yahoo Finance (ticker ^NSEI), pulled via yfinance.
Why Yahoo/yfinance:
  - Free, no auth/API key needed
  - Widely used, easy to cite and reproduce (anyone can rerun this script)
  - Covers ~2007-present at daily granularity for ^NSEI reliably;
    pre-2007 exists but has more gaps -> we document whatever range we
    actually get after validation, not assume a range in advance.

Run:
    pip install yfinance
    python get_data.py

Output:
    ../data/nifty_raw.csv   (Date, Open, High, Low, Close, Volume)
"""

import yfinance as yf
import pandas as pd
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "nifty_raw.csv"
TICKER = "^NSEI"

def fetch():
    print(f"Downloading {TICKER} full daily history from Yahoo Finance...")
    df = yf.download(TICKER, period="max", interval="1d", auto_adjust=False, progress=False)

    if df.empty:
        raise RuntimeError("No data returned. Check ticker/network.")

    # yfinance sometimes returns MultiIndex columns when a single ticker
    # is passed as part of newer versions -> flatten defensively.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()  # Date becomes a column
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"Saved {len(df)} rows to {OUT_PATH}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")

if __name__ == "__main__":
    fetch()
