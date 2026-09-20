"""
Task 7 — simple event-driven backtest.

Explicitly NOT a sophisticated framework (assignment says not to build
one). One strategy: on each independent event, enter at next-day open,
exit at close after HOLDING_DAYS, full capital in/out per trade
(no overlap handling beyond skipping a new entry if already in a
position), cost applied on both entry and exit.

Given the research findings (no statistically robust recovery effect;
sign/significance did not survive the OOS split), this backtest is run
as the assignment's extension of the research, NOT as a claim that this
is a tradable strategy. The honest expectation going in is a result
indistinguishable from noise/costs -- and the code does not need to
"succeed" for the assignment to succeed.
"""

import numpy as np
import pandas as pd
from config import CONFIG
from event_engine import load_data, detect_events

HOLDING_DAYS = 5  # pick one horizon for the backtest; keep it simple per the brief


def run_backtest(df, events, holding_days=HOLDING_DAYS, cost_bps_per_side=None):
    cost_bps_per_side = CONFIG["cost_bps_per_side"] if cost_bps_per_side is None else cost_bps_per_side
    cost_frac = cost_bps_per_side / 10000

    indep_events = events[events["is_independent"]].sort_values("event_idx")
    n = len(df)

    trades = []
    last_exit_idx = -1  # enforce no overlapping trades: skip a signal while already in a position

    for _, ev in indep_events.iterrows():
        entry_idx = ev["event_idx"] + CONFIG["entry_lag"]
        exit_idx = entry_idx + holding_days - 1

        if entry_idx <= last_exit_idx:
            continue  # would overlap an open position -> skip (simple, conservative choice)
        if exit_idx >= n:
            continue  # not enough data left to complete the trade

        entry_price = df.loc[entry_idx, "Open"]
        exit_price = df.loc[exit_idx, "Close"]
        gross_ret = exit_price / entry_price - 1
        net_ret = (1 + gross_ret) * (1 - cost_frac) * (1 - cost_frac) - 1  # cost on entry and exit

        trades.append({
            "event_date": ev["event_date"], "entry_date": df.loc[entry_idx, "Date"],
            "exit_date": df.loc[exit_idx, "Date"], "entry_price": entry_price,
            "exit_price": exit_price, "gross_return": gross_ret, "net_return": net_ret,
        })
        last_exit_idx = exit_idx

    trades_df = pd.DataFrame(trades)
    return trades_df


def summarize(trades_df):
    if len(trades_df) == 0:
        print("No trades generated.")
        return

    n_trades = len(trades_df)
    win_rate = (trades_df["net_return"] > 0).mean()

    # cumulative equity assuming full capital reinvested each trade, sequentially
    equity = (1 + trades_df["net_return"]).cumprod()
    equity_gross = (1 + trades_df["gross_return"]).cumprod()

    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_dd = drawdown.min()

    total_return_net = equity.iloc[-1] - 1
    total_return_gross = equity_gross.iloc[-1] - 1

    print(f"Number of trades:        {n_trades}")
    print(f"Win rate (net of costs): {win_rate:.2%}")
    print(f"Mean net return/trade:   {trades_df['net_return'].mean():+.4%}")
    print(f"Total return (gross):    {total_return_gross:+.2%}")
    print(f"Total return (net):      {total_return_net:+.2%}")
    print(f"Max drawdown (net eq.):  {max_dd:.2%}")
    print(f"Cost drag (gross-net):   {(total_return_gross - total_return_net):+.2%}")

    return {
        "n_trades": n_trades, "win_rate": win_rate,
        "mean_net_return": trades_df["net_return"].mean(),
        "total_return_gross": total_return_gross, "total_return_net": total_return_net,
        "max_drawdown": max_dd,
    }


if __name__ == "__main__":
    df = load_data()
    events = detect_events(df)
    trades_df = run_backtest(df, events, holding_days=HOLDING_DAYS)

    print(f"=== BACKTEST: threshold={CONFIG['event_threshold']:.1%}, "
          f"holding={HOLDING_DAYS}d, cost={CONFIG['cost_bps_per_side']}bps/side ===\n")
    stats = summarize(trades_df)

    # Context, not a fair benchmark: the strategy is only in the market for
    # n_trades * holding_days days out of the full sample, so its total
    # return is NOT directly comparable to buy-and-hold. Shown for scale only.
    if len(trades_df) > 0:
        bh_start, bh_end = df["Close"].iloc[0], df["Close"].iloc[-1]
        bh_total_return = bh_end / bh_start - 1
        days_in_market = len(trades_df) * HOLDING_DAYS
        print(f"\n[Context, not a benchmark] Buy-and-hold over full sample: {bh_total_return:+.2%}")
        print(f"[Context] Strategy was in the market ~{days_in_market} of {len(df)} trading days "
              f"({days_in_market/len(df):.1%} of the time)")

    import os
    os.makedirs("../results", exist_ok=True)
    trades_df.to_csv("../results/backtest_trades.csv", index=False)
    print("\nSaved: ../results/backtest_trades.csv")
