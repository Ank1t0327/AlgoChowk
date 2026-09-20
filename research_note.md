# Research Note: Does NIFTY Recover After a Significant One-Day Fall?

## 1. Hypothesis

After a significant one-day fall in NIFTY, the market tends to recover over
the next few trading days.

**Operationalized as:** conditional on a day where NIFTY's close-to-close
return falls below a threshold, the forward return over a fixed holding
period (measured from the next tradable entry) is systematically higher
than NIFTY's unconditional forward return over the same horizon.

## 2. Event & Recovery Definitions

- **Event:** day *t* where `r_t = Close_t / Close_{t-1} - 1 ≤ -3%` (primary
  threshold; swept over -1.5% to -5% for robustness, Section 5).
- **Independence:** an event within 3 trading days of a prior event is
  flagged *clustered*, not independent. Clustered events (e.g. three -3%+
  days across the Jan 2008 crash) are analyzed both included and excluded,
  since treating each as an independent draw overstates effective sample
  size.
- **Recovery — two definitions, kept separate:**
  1. *Statistical:* mean/median forward return over the holding period is
     positive, win rate > 50%.
  2. *Practical:* `Close` within the holding period climbs back to or above
     `Close_{t-1}` (the pre-fall level) — whether the loss was actually
     erased, which (1) can mask.

## 3. Entry / Exit

Entry at `Open_{t+1}` — the fall is only confirmed at the close of day *t*,
so entering at `Close_t` would be look-ahead bias. Exit at `Close` after
the holding period, no intraday assumptions.

## 4. Holding Period

N ∈ {1, 3, 5, 10} trading days, evaluated independently — no single N was
picked in advance as "the" answer.

## 5. Test Period

Full available NIFTY daily history: **2007-09-17 to 2026-09-18** (4,663
rows, sourced via Yahoo Finance `^NSEI`, validated for gaps/duplicates/OHLC
consistency — none found). Split for out-of-sample validation at
**2019-12-31**: research period (2007–2019, 3,001 rows, contains the 2008
GFC) vs. out-of-sample period (2020–2026, 1,662 rows, contains the 2020
COVID crash). Event threshold and holding periods were fixed from the
research period and **not retuned** on the OOS slice.

## 6. Transaction Costs

5 bps per side (10 bps round-trip), applied on both entry and exit in the
backtest — a conservative estimate for index-proxy execution, not
optimized to flatter results.

## 7. Key Assumptions

- Full capital per trade, no overlapping positions (a new signal during an
  open position is skipped).
- No dividends/index reconstitution effects modeled (price index only).
- Baseline for comparison is the forward return of *every* day in the
  sample (not just event days) at the same horizon — NIFTY drifts upward
  over this period, so "recovers within N days" must beat that drift to
  mean anything.

## 8. Evidence Summary

At the primary threshold (-3%), **no holding period shows a statistically
distinguishable difference from baseline** (permutation p = 0.12–0.94,
n = 59–79 events). A sweep across 7 thresholds × 4 holding periods (28
cells) surfaces two "significant" cells (-2.5%/10d positive, -5%/3–10d
negative) — but neither is flanked by a consistent pattern in neighboring
thresholds, which is the signature of a false positive from multiple
testing (at α=0.05 across 28 tests, 1–2 hits are expected by chance alone).

The out-of-sample split makes this concrete: the research period shows a
significant *negative* 1-day effect (p=0.024, falls continue rather than
reverse), while the OOS period shows a significant *positive* 3-day effect
(p=0.015) — opposite signs, different horizons, neither replicating the
other. The relationship does not survive contact with unseen data.

## Conclusion

The data does not support a robust post-fall recovery effect in NIFTY
beyond what general upward drift explains. This is treated as a genuine
negative result, not a failure of the analysis — see README for full
limitations and the case for rejecting the hypothesis as stated.
