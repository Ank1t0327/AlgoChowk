"""
Validate the raw NIFTY daily OHLC file before any event detection.

Checks:
    - row count, date range, trading-day coverage
    - duplicate dates
    - date ordering
    - missing/NaN OHLC values
    - OHLC internal consistency (High >= Low, High >= Open/Close, Low <= Open/Close)
    - zero/negative prices
    - suspicious single-day jumps (|return| > threshold) for manual review
    - daily returns computed on Close

Run:
    python inspect_data.py ../data/nifty_raw.csv
"""

import sys
import pandas as pd
import numpy as np

def load(path):
    df = pd.read_csv(path, parse_dates=["Date"])
    return df

def report(df):
    print("=" * 60)
    print("ROW COUNT:", len(df))
    print("DATE RANGE:", df["Date"].min().date(), "to", df["Date"].max().date())

    # duplicates
    dupes = df[df.duplicated(subset="Date", keep=False)]
    print(f"\nDUPLICATE DATES: {df['Date'].duplicated().sum()}")
    if len(dupes):
        print(dupes.sort_values("Date").head(10))

    # ordering
    is_sorted = df["Date"].is_monotonic_increasing
    print(f"\nDATE ORDER MONOTONIC INCREASING: {is_sorted}")
    if not is_sorted:
        bad = df[df["Date"].diff().dt.days < 0]
        print("Out-of-order rows (first 10):")
        print(bad.head(10))

    # missing values
    print("\nMISSING VALUES PER COLUMN:")
    print(df[["Open", "High", "Low", "Close"]].isna().sum())

    # zero / negative
    for col in ["Open", "High", "Low", "Close"]:
        bad = df[df[col] <= 0]
        if len(bad):
            print(f"\n{col}: {len(bad)} rows with value <= 0")

    # OHLC consistency
    inconsistent = df[
        (df["High"] < df["Low"]) |
        (df["High"] < df["Open"]) |
        (df["High"] < df["Close"]) |
        (df["Low"] > df["Open"]) |
        (df["Low"] > df["Close"])
    ]
    print(f"\nOHLC INTERNAL INCONSISTENCIES: {len(inconsistent)}")
    if len(inconsistent):
        print(inconsistent.head(10))

    # trading day coverage vs expected (rough: NSE trading days ~ 245-250/yr)
    df_sorted = df.sort_values("Date").reset_index(drop=True)
    years = df_sorted["Date"].dt.year
    per_year = years.value_counts().sort_index()
    print("\nROWS PER YEAR (spot-check against ~245-250 typical trading days):")
    print(per_year)

    # daily returns
    df_sorted["ret"] = df_sorted["Close"].pct_change()
    print("\nDAILY RETURN STATS:")
    print(df_sorted["ret"].describe())

    # suspicious jumps
    thresh = 0.10  # 10% single-day move on the index level is rare/suspicious pre-filter
    suspicious = df_sorted[df_sorted["ret"].abs() > thresh]
    print(f"\nSUSPICIOUS |return| > {thresh:.0%}: {len(suspicious)} rows")
    if len(suspicious):
        print(suspicious[["Date", "Open", "High", "Low", "Close", "ret"]])

    return df_sorted

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../data/nifty_raw.csv"
    df = load(path)
    report(df)
