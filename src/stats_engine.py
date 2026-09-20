"""
Task 3 — statistical evidence.

Why bootstrap/permutation over a plain t-test as the PRIMARY method:
  - Forward returns are not i.i.d. normal: they're skewed, fat-tailed,
    and overlapping (a 10d forward return computed daily shares 9 days
    of data with the next one; event windows can overlap too when
    events cluster). A t-test's CI is untrustworthy under these
    conditions.
  - Bootstrap CIs and a permutation test make no distributional
    assumption, and the permutation test directly answers "could this
    gap between event-day and baseline forward returns be a fluke of
    which days got labeled 'event'?" without pretending the samples
    are independent draws from a normal.
  - A plain Welch's t-test is still reported alongside as a common
    diagnostic reviewers expect to see, with the caveat above stated
    explicitly rather than silently relied on.

This does NOT correct for event clustering (Task 4 handles that by
re-running everything on the is_independent-only subset) or for the
autocorrelation in the baseline pool — both are named as limitations,
not hidden.
"""

import numpy as np
import pandas as pd
from scipy import stats as sstats

from config import CONFIG
from event_engine import load_data, detect_events, compute_forward_returns, compute_baseline_forward_returns

RNG = np.random.default_rng(42)  # fixed seed -> reproducible bootstrap/permutation numbers


def bootstrap_mean_ci(data, n_boot=10000, alpha=0.05, rng=RNG):
    data = np.asarray(pd.Series(data).dropna())
    if len(data) == 0:
        return np.nan, np.nan, np.nan
    boot_means = rng.choice(data, size=(n_boot, len(data)), replace=True).mean(axis=1)
    lo, hi = np.percentile(boot_means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return data.mean(), lo, hi


def bootstrap_proportion_ci(bool_series, n_boot=10000, alpha=0.05, rng=RNG):
    data = np.asarray(pd.Series(bool_series).dropna().astype(float))
    if len(data) == 0:
        return np.nan, np.nan, np.nan
    boot_props = rng.choice(data, size=(n_boot, len(data)), replace=True).mean(axis=1)
    lo, hi = np.percentile(boot_props, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return data.mean(), lo, hi


def permutation_test_diff_means(sample_a, sample_b, n_perm=10000, rng=RNG):
    """
    H0: sample_a and sample_b are drawn from the same distribution
    (i.e. being an "event day" carries no information about the forward
    return). Returns (observed_diff, p_value_two_sided).
    """
    a = np.asarray(pd.Series(sample_a).dropna())
    b = np.asarray(pd.Series(sample_b).dropna())
    observed = a.mean() - b.mean()

    pooled = np.concatenate([a, b])
    n_a = len(a)
    diffs = np.empty(n_perm)
    for i in range(n_perm):
        rng.shuffle(pooled)
        diffs[i] = pooled[:n_a].mean() - pooled[n_a:].mean()

    p_value = (np.abs(diffs) >= np.abs(observed)).mean()
    return observed, p_value


def welch_t_test(sample_a, sample_b):
    a = np.asarray(pd.Series(sample_a).dropna())
    b = np.asarray(pd.Series(sample_b).dropna())
    t_stat, p_value = sstats.ttest_ind(a, b, equal_var=False)
    return t_stat, p_value


def run_full_analysis(events, baseline, holding_periods=None, label="ALL EVENTS"):
    holding_periods = CONFIG["holding_periods"] if holding_periods is None else holding_periods
    rows = []
    print(f"\n{'=' * 70}\n{label} (n={len(events)})\n{'=' * 70}")

    for N in holding_periods:
        col = f"fwd_ret_{N}d"
        rec_col = f"recovered_{N}d"

        event_ret = events[col].dropna()
        baseline_ret = baseline[col].dropna()

        mean, lo, hi = bootstrap_mean_ci(event_ret)
        win_mean, win_lo, win_hi = bootstrap_proportion_ci(event_ret > 0)
        rec_mean, rec_lo, rec_hi = bootstrap_proportion_ci(events[rec_col])

        diff, perm_p = permutation_test_diff_means(event_ret, baseline_ret)
        t_stat, t_p = welch_t_test(event_ret, baseline_ret)

        print(f"\n--- {N}-day holding period (n_events={len(event_ret)}, n_baseline={len(baseline_ret)}) ---")
        print(f"  Event mean fwd return:    {mean:+.4%}  [95% CI {lo:+.4%}, {hi:+.4%}]")
        print(f"  Baseline mean fwd return: {baseline_ret.mean():+.4%}")
        print(f"  Win rate (event):         {win_mean:.2%}  [95% CI {win_lo:.2%}, {win_hi:.2%}]")
        print(f"  Practical recovery rate:  {rec_mean:.2%}  [95% CI {rec_lo:.2%}, {rec_hi:.2%}]")
        print(f"  Diff (event - baseline):  {diff:+.4%}   permutation p={perm_p:.4f}   Welch t-test p={t_p:.4f}")

        rows.append({
            "holding_days": N, "n_events": len(event_ret), "n_baseline": len(baseline_ret),
            "event_mean": mean, "event_ci_lo": lo, "event_ci_hi": hi,
            "baseline_mean": baseline_ret.mean(),
            "win_rate": win_mean, "win_ci_lo": win_lo, "win_ci_hi": win_hi,
            "recovery_rate": rec_mean, "recovery_ci_lo": rec_lo, "recovery_ci_hi": rec_hi,
            "diff_vs_baseline": diff, "permutation_p": perm_p, "welch_t_p": t_p,
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load_data()
    events = detect_events(df)
    results = compute_forward_returns(df, events)
    baseline = compute_baseline_forward_returns(df)

    summary_all = run_full_analysis(results, baseline, label="ALL EVENTS (incl. clustered)")

    independent_only = results[results["is_independent"]]
    summary_indep = run_full_analysis(independent_only, baseline, label="INDEPENDENT EVENTS ONLY")

    import os
    os.makedirs("../results", exist_ok=True)
    summary_all.to_csv("../results/stats_summary_all_events.csv", index=False)
    summary_indep.to_csv("../results/stats_summary_independent_events.csv", index=False)
    print("\nSaved: ../results/stats_summary_all_events.csv, ../results/stats_summary_independent_events.csv")
