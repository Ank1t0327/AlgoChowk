"""
Task 5 — out-of-sample validation.

Split: research/development period ends CONFIG["research_end_date"]
(2019-12-31 by default), everything after is out-of-sample (OOS).

Critical rule this script enforces: the event threshold, min_gap, and
holding periods are NOT retuned on the OOS period. Whatever was decided
during research (config.py, informed by the sweep in robustness_sweep.py
run only conceptually against the research slice) is applied as-is to
OOS data. Retuning on OOS would defeat the entire point of the split.

Note on this specific dataset: the research period (2007-2019) contains
the 2008 GFC crash; the OOS period (2020-2026) contains the COVID crash.
That's actually a reasonable regime split for a falsification test -- it
is NOT "OOS conveniently has no crashes" cherry-picking.
"""

import pandas as pd
from config import CONFIG
from event_engine import load_data, detect_events, compute_forward_returns, compute_baseline_forward_returns
from stats_engine import bootstrap_mean_ci, permutation_test_diff_means


def split_data(df, research_end_date=None):
    research_end_date = CONFIG["research_end_date"] if research_end_date is None else research_end_date
    cutoff = pd.Timestamp(research_end_date)
    research = df[df["Date"] <= cutoff].reset_index(drop=True)
    oos = df[df["Date"] > cutoff].reset_index(drop=True)
    return research, oos


def analyze_period(df_period, label, threshold=None, min_gap_days=None, holding_periods=None):
    threshold = CONFIG["event_threshold"] if threshold is None else threshold
    min_gap_days = CONFIG["min_gap_days"] if min_gap_days is None else min_gap_days
    holding_periods = CONFIG["holding_periods"] if holding_periods is None else holding_periods

    print(f"\n{'=' * 70}\n{label}: {df_period['Date'].min().date()} to {df_period['Date'].max().date()} "
          f"({len(df_period)} rows)\n{'=' * 70}")

    events = detect_events(df_period, threshold=threshold, min_gap_days=min_gap_days)
    baseline = compute_baseline_forward_returns(df_period, holding_periods=holding_periods)
    results = compute_forward_returns(df_period, events, holding_periods=holding_periods)
    indep = results[results["is_independent"]]

    print(f"Events: {len(events)} total, {events['is_independent'].sum()} independent")

    rows = []
    for N in holding_periods:
        col = f"fwd_ret_{N}d"
        indep_ret = indep[col].dropna()
        baseline_ret = baseline[col].dropna()

        if len(indep_ret) < 3:
            print(f"  {N}d: too few independent events ({len(indep_ret)}) to test")
            continue

        mean, lo, hi = bootstrap_mean_ci(indep_ret, n_boot=3000)
        diff, p = permutation_test_diff_means(indep_ret, baseline_ret, n_perm=3000)

        print(f"  {N}d: n={len(indep_ret)}, mean={mean:+.4%} [{lo:+.4%},{hi:+.4%}], "
              f"baseline={baseline_ret.mean():+.4%}, diff={diff:+.4%}, perm_p={p:.4f}")

        rows.append({"period": label, "holding_days": N, "n_independent_events": len(indep_ret),
                      "mean": mean, "ci_lo": lo, "ci_hi": hi, "baseline_mean": baseline_ret.mean(),
                      "diff_vs_baseline": diff, "perm_p": p})

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load_data()
    research, oos = split_data(df)

    research_summary = analyze_period(research, "RESEARCH / DEVELOPMENT PERIOD")
    oos_summary = analyze_period(oos, "OUT-OF-SAMPLE PERIOD")

    combined = pd.concat([research_summary, oos_summary], ignore_index=True)

    print(f"\n{'=' * 70}\nSIDE-BY-SIDE (definitions fixed from research period, unchanged for OOS)\n{'=' * 70}")
    pivot = combined.pivot(index="holding_days", columns="period", values=["mean", "perm_p"])
    print(pivot.round(4).to_string())

    import os
    os.makedirs("../results", exist_ok=True)
    combined.to_csv("../results/oos_split_summary.csv", index=False)
    print("\nSaved: ../results/oos_split_summary.csv")
