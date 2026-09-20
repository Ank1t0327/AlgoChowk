"""
Event detection and forward-return computation for the NIFTY post-fall
recovery hypothesis. Everything reads from a config dict (see config.py)
so changing the event threshold or holding periods never requires
touching this file.
"""

import pandas as pd
import numpy as np
from config import CONFIG


def load_data(path=None):
    path = path or CONFIG["data_path"]
    df = pd.read_csv(path, parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    df["ret"] = df["Close"].pct_change()
    return df


def detect_events(df, threshold=None, min_gap_days=None):
    """
    Returns a DataFrame of events: one row per qualifying day, with
    - event_idx: row index in df
    - event_date, event_return
    - is_independent: False if within min_gap_days of a prior event
    """
    threshold = CONFIG["event_threshold"] if threshold is None else threshold
    min_gap_days = CONFIG["min_gap_days"] if min_gap_days is None else min_gap_days

    mask = df["ret"] <= threshold
    events = df.loc[mask, ["Date", "ret"]].copy()
    events = events.rename(columns={"Date": "event_date", "ret": "event_return"})
    events["event_idx"] = events.index

    # independence flag: gap (in row/trading-day count) since previous event
    idxs = events["event_idx"].to_numpy()
    gaps = np.diff(idxs, prepend=-min_gap_days - 1)
    events["gap_since_prev_event"] = gaps
    events["is_independent"] = gaps >= min_gap_days

    return events.reset_index(drop=True)


def compute_forward_returns(df, events, holding_periods=None, entry_lag=None):
    """
    For each event, compute:
      - entry_idx / entry_date / entry_price (Open at event_idx + entry_lag)
      - for each N in holding_periods: forward return from entry_price to
        Close at entry_idx + N - 1 (i.e. N trading days held, exiting at close)
      - recovered_N: whether Close at that exit point >= Close at event_idx - 1
        (the pre-fall close) -> the "practical" recovery definition
    Events too close to the end of the data to compute a given holding
    period are left as NaN for that column (documented, not dropped).
    """
    holding_periods = CONFIG["holding_periods"] if holding_periods is None else holding_periods
    entry_lag = CONFIG["entry_lag"] if entry_lag is None else entry_lag

    n = len(df)
    out = events.copy()

    entry_idx = out["event_idx"] + entry_lag
    valid_entry = entry_idx < n
    out["entry_idx"] = entry_idx.where(valid_entry)
    out["entry_date"] = out["entry_idx"].map(lambda i: df.loc[i, "Date"] if pd.notna(i) else pd.NaT)
    out["entry_price"] = out["entry_idx"].map(lambda i: df.loc[i, "Open"] if pd.notna(i) else np.nan)

    pre_fall_close = out["event_idx"].map(lambda i: df.loc[i - 1, "Close"] if i - 1 >= 0 else np.nan)
    out["pre_fall_close"] = pre_fall_close

    for N in holding_periods:
        exit_idx = out["entry_idx"] + (N - 1)
        valid = exit_idx.notna() & (exit_idx < n)

        exit_price = pd.Series(np.nan, index=out.index)
        exit_price[valid] = exit_idx[valid].map(lambda i: df.loc[int(i), "Close"])

        fwd_ret = exit_price / out["entry_price"] - 1
        out[f"fwd_ret_{N}d"] = fwd_ret
        recovered = (exit_price >= out["pre_fall_close"]).astype("boolean")
        recovered[~valid] = pd.NA
        out[f"recovered_{N}d"] = recovered

    return out


def compute_baseline_forward_returns(df, holding_periods=None, entry_lag=None):
    """
    Same forward-return calculation as compute_forward_returns, applied to
    EVERY day in df (not just event days). This is the baseline population
    that event-day forward returns get compared against — the whole point
    being: NIFTY drifts up on average, so a positive mean forward return
    after an "event" means nothing unless it beats this baseline.
    """
    holding_periods = CONFIG["holding_periods"] if holding_periods is None else holding_periods
    entry_lag = CONFIG["entry_lag"] if entry_lag is None else entry_lag

    n = len(df)
    out = pd.DataFrame({"date": df["Date"]})
    entry_idx = pd.Series(np.arange(n)) + entry_lag
    valid_entry = entry_idx < n
    entry_price = entry_idx.where(valid_entry).map(lambda i: df.loc[i, "Open"] if pd.notna(i) else np.nan)

    for N in holding_periods:
        exit_idx = entry_idx + (N - 1)
        valid = valid_entry & (exit_idx < n)
        exit_price = pd.Series(np.nan, index=out.index)
        exit_price[valid] = exit_idx[valid].map(lambda i: df.loc[int(i), "Close"])
        out[f"fwd_ret_{N}d"] = exit_price / entry_price - 1

    return out


if __name__ == "__main__":
    df = load_data()
    events = detect_events(df)
    print(f"Events detected: {len(events)} (threshold={CONFIG['event_threshold']:.1%})")
    print(f"Independent events (gap >= {CONFIG['min_gap_days']}d): {events['is_independent'].sum()}")
    print(events.head(10))

    results = compute_forward_returns(df, events)
    print("\nForward return summary by holding period:")
    for N in CONFIG["holding_periods"]:
        col = f"fwd_ret_{N}d"
        rec = f"recovered_{N}d"
        valid = results[col].dropna()
        print(f"\n  {N}d: n={len(valid)}, mean={valid.mean():.4f}, median={valid.median():.4f}, "
              f"win_rate={(valid > 0).mean():.2%}, recovered_rate={results[rec].dropna().mean():.2%}")

    baseline = compute_baseline_forward_returns(df)
    print("\nBaseline (all days) forward return summary:")
    for N in CONFIG["holding_periods"]:
        col = f"fwd_ret_{N}d"
        valid = baseline[col].dropna()
        print(f"  {N}d: mean={valid.mean():.4f}, median={valid.median():.4f}, win_rate={(valid > 0).mean():.2%}")
