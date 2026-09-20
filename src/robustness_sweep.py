"""
Task 4 — robustness / sensitivity sweep.

Runs the full detect -> forward-return -> stats pipeline across a grid
of event thresholds, so the -3% choice isn't a single cherry-picked
number. This is diagnostic, not a search for the best-looking result —
report the whole table, not just whichever row has the smallest p-value
(that would be exactly the data-snooping/post-hoc selection the
assignment tells you to discuss and avoid).
"""

import numpy as np
import pandas as pd

from config import CONFIG
from event_engine import load_data, detect_events, compute_forward_returns, compute_baseline_forward_returns
from stats_engine import bootstrap_mean_ci, permutation_test_diff_means

THRESHOLD_GRID = [-0.015, -0.02, -0.025, -0.03, -0.035, -0.04, -0.05]
MIN_GAP_GRID = [1, 3, 5]  # how strict "independent" means


def sweep_thresholds(df, baseline, holding_periods=None, min_gap_days=None):
    holding_periods = CONFIG["holding_periods"] if holding_periods is None else holding_periods
    min_gap_days = CONFIG["min_gap_days"] if min_gap_days is None else min_gap_days

    rows = []
    for thresh in THRESHOLD_GRID:
        events = detect_events(df, threshold=thresh, min_gap_days=min_gap_days)
        if len(events) < 5:
            continue  # too few events to say anything
        results = compute_forward_returns(df, events)
        indep = results[results["is_independent"]]

        for N in holding_periods:
            col = f"fwd_ret_{N}d"
            event_ret = results[col].dropna()
            indep_ret = indep[col].dropna()
            baseline_ret = baseline[col].dropna()

            mean_all, lo_all, hi_all = bootstrap_mean_ci(event_ret, n_boot=2000)
            _, p_all = permutation_test_diff_means(event_ret, baseline_ret, n_perm=2000)

            mean_ind, lo_ind, hi_ind = bootstrap_mean_ci(indep_ret, n_boot=2000)
            _, p_ind = permutation_test_diff_means(indep_ret, baseline_ret, n_perm=2000)

            rows.append({
                "threshold": thresh, "holding_days": N,
                "n_events_all": len(event_ret), "mean_all": mean_all,
                "ci_lo_all": lo_all, "ci_hi_all": hi_all, "perm_p_all": p_all,
                "n_events_indep": len(indep_ret), "mean_indep": mean_ind,
                "ci_lo_indep": lo_ind, "ci_hi_indep": hi_ind, "perm_p_indep": p_ind,
                "baseline_mean": baseline_ret.mean(),
            })

    return pd.DataFrame(rows)


def sweep_min_gap(df, baseline, threshold=None, holding_periods=None):
    """Holds threshold fixed, varies how strict the independence filter is."""
    threshold = CONFIG["event_threshold"] if threshold is None else threshold
    holding_periods = CONFIG["holding_periods"] if holding_periods is None else holding_periods

    rows = []
    for gap in MIN_GAP_GRID:
        events = detect_events(df, threshold=threshold, min_gap_days=gap)
        results = compute_forward_returns(df, events)
        indep = results[results["is_independent"]]

        for N in holding_periods:
            col = f"fwd_ret_{N}d"
            indep_ret = indep[col].dropna()
            baseline_ret = baseline[col].dropna()
            mean, lo, hi = bootstrap_mean_ci(indep_ret, n_boot=2000)
            _, p = permutation_test_diff_means(indep_ret, baseline_ret, n_perm=2000)
            rows.append({
                "min_gap_days": gap, "holding_days": N, "n_independent_events": len(indep_ret),
                "mean": mean, "ci_lo": lo, "ci_hi": hi, "perm_p": p,
            })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load_data()
    baseline = compute_baseline_forward_returns(df)

    print("Running threshold sweep (this takes a bit -- permutation tests per cell)...")
    thresh_results = sweep_thresholds(df, baseline)
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 20)
    print("\n=== THRESHOLD SWEEP ===")
    print(thresh_results[["threshold", "holding_days", "n_events_all", "mean_all", "perm_p_all",
                           "n_events_indep", "mean_indep", "perm_p_indep", "baseline_mean"]]
          .round(5).to_string(index=False))

    print("\nRunning independence-strictness sweep at default threshold...")
    gap_results = sweep_min_gap(df, baseline)
    print("\n=== MIN-GAP SWEEP (threshold fixed at default) ===")
    print(gap_results.round(5).to_string(index=False))

    import os
    os.makedirs("../results", exist_ok=True)
    thresh_results.to_csv("../results/robustness_threshold_sweep.csv", index=False)
    gap_results.to_csv("../results/robustness_mingap_sweep.csv", index=False)
    print("\nSaved: ../results/robustness_threshold_sweep.csv, ../results/robustness_mingap_sweep.csv")
