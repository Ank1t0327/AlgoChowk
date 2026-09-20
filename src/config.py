"""
Single place to change the experiment's knobs. Nothing downstream should
hardcode a threshold or holding period — everything reads from here (or
from a CONFIG dict passed explicitly), so re-running with a different
definition of "significant fall" or a different holding period never
means rewriting detect_events / compute_forward_returns.
"""

CONFIG = {
    # Event definition
    "event_threshold": -0.03,       # close-to-close return <= this -> event
    "min_gap_days": 3,              # trading days since last event to count as independent

    # Execution
    "entry_lag": 1,                 # enter at Open of t + entry_lag (t=event day)

    # Analysis
    "holding_periods": [1, 3, 5, 10],   # trading days forward from entry

    # Costs (round-trip, in decimal, applied once per entry+exit in the backtest)
    "cost_bps_per_side": 5,         # 5 bps = 0.05% per side (slippage+brokerage, index proxy)

    # Data
    "data_path": "../data/nifty_raw.csv",

    # Out-of-sample split (date string, inclusive research end)
    "research_end_date": "2019-12-31",
}
