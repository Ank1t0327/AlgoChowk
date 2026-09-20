# AlgoChowk Quant Engineer Assignment — NIFTY Post-Fall Recovery

Investigating: *"After a significant one-day fall in NIFTY, the market
tends to recover over the next few trading days."*

**Short answer: no robust evidence supports this.** See `research_note.md`
for the full write-up; this README covers reproduction, methodology
detail, complete results, and limitations.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Reproducing the results

Run from `src/`, in order:

```bash
cd src
python get_data.py          # pulls NIFTY (^NSEI) daily OHLC via yfinance -> ../data/nifty_raw.csv
python inspect_data.py      # data validation report (printed, not saved)
python event_engine.py      # event detection + forward returns (printed)
python stats_engine.py      # bootstrap CIs + permutation tests -> ../results/stats_summary_*.csv
python robustness_sweep.py  # threshold & min-gap sensitivity   -> ../results/robustness_*.csv
python oos_split.py         # out-of-sample validation          -> ../results/oos_split_summary.csv
python backtest.py          # simple event-driven backtest      -> ../results/backtest_trades.csv
```

All parameters (event threshold, holding periods, min gap, entry lag,
costs, OOS split date) live in `src/config.py` — nothing needs code
changes to re-run with different assumptions.

## Data

- **Source:** Yahoo Finance, ticker `^NSEI`, via `yfinance`.
- **Range:** 2007-09-17 to 2026-09-18, 4,663 daily rows.
- **Fields:** Date, Open, High, Low, Close, Volume.
- **Validation:** no duplicate dates, no missing OHLC values, dates
  strictly increasing, no internal OHLC inconsistencies (High/Low bounds
  respected). 3 single-day moves exceed 10% (2008-10-24 GFC, 2009-05-18
  election-result rally/circuit, 2020-03-23 COVID crash) — confirmed as
  real market events, not data errors, and retained.

## Methodology

See `research_note.md` §1–7 for full definitions. Summary:

| Item | Definition |
|---|---|
| Event | `Close_t/Close_{t-1} - 1 ≤ -3%` (swept -1.5% to -5%) |
| Independence | ≥3 trading days since prior event (swept 1/3/5) |
| Entry | `Open_{t+1}` |
| Exit | `Close` after holding period |
| Holding periods | 1, 3, 5, 10 trading days |
| Costs | 5 bps/side, applied entry + exit |
| Baseline | forward return of every day in sample, same horizon |
| OOS split | research ≤2019-12-31, OOS 2020-01-01 onward, definitions fixed from research period only |

## Results

### Primary threshold (-3%), all events vs. independent-only

| Holding | n (indep) | Mean fwd ret | vs. baseline | Permutation p | Practical recovery rate |
|---|---|---|---|---|---|
| 1d | 59 | -0.29% | -0.24pp | 0.12 | 1.7% |
| 3d | 59 | +0.21% | +0.17pp | 0.56 | 18.6% |
| 5d | 59 | +0.31% | +0.19pp | 0.61 | 28.8% |
| 10d | 59 | +0.08% | -0.25pp | 0.64 | 40.7% |

No horizon is statistically distinguishable from baseline. "Practical
recovery rate" rises with N mostly because NIFTY has a positive long-run
drift over this sample, not because of a fall-specific effect.

### Robustness sweep (7 thresholds × 4 holding periods, 28 cells)

Two cells cross p<0.05 (-2.5%/10d positive, -5%/3–10d negative), but
neither is supported by neighboring thresholds — consistent with
multiple-testing noise (≈1–2 false positives expected at α=0.05 across 28
tests), not a real effect. Full table: `results/robustness_threshold_sweep.csv`.

### Out-of-sample validation

Definitions fixed from the research period (2007–2019), applied unchanged
to 2020–2026:

| Period | Significant cell | Direction |
|---|---|---|
| Research (2007–2019) | 1d, p=0.024 | **Negative** (falls continue) |
| OOS (2020–2026) | 3d, p=0.015 | **Positive** (partial reversal) |

Neither the sign, the horizon, nor the significance carries over between
periods — the strongest evidence against a robust effect. Full table:
`results/oos_split_summary.csv`.

### Simple backtest (-3% threshold, 5d hold, independent events only)

| Metric | Value |
|---|---|
| Trades | 54 |
| Win rate (net) | 57.4% |
| Mean net return/trade | +0.67% |
| Total return, net | +34.5% |
| Total return, gross | +42.0% |
| Max drawdown | -33.0% |
| Buy-and-hold, same period (context only) | +419.4% |
| Time in market | 5.8% |

**Not a tradable strategy.** The headline return looks positive only in
isolation — it is not statistically distinguishable from noise (see
above), does not survive out-of-sample, and the drawdown is driven by
correlated losses during the 2008 event cluster rather than genuine risk
exposure to a working edge.

## Limitations

- **Small sample.** 59–79 independent events over 19 years; every p-value
  and CI in this repo should be read with that in mind. This is a data
  constraint of the hypothesis itself (large falls are rare), not a
  methodology gap.
- **Event clustering.** Crashes produce multiple qualifying days in quick
  succession (e.g. Jan 2008, three events in a week). The independence
  filter mitigates but does not fully solve this — clustered events still
  share macro conditions even when 3+ trading days apart.
- **Baseline autocorrelation.** The all-days baseline uses overlapping
  N-day windows (consecutive days share N-1 days of return), so its
  variance is understated relative to truly independent draws. This makes
  the permutation test somewhat conservative in the baseline's favor, not
  in the event sample's favor — doesn't change the "no effect" conclusion
  but is worth naming.
- **Single index, single market.** Findings say nothing about other
  indices, individual stocks, or non-Indian markets.
- **No dividend/reconstitution adjustment.** Price-index effects only.
- **Backtest costs are a flat estimate** (5 bps/side), not modeled from
  actual bid-ask/impact data, and could understate real-world costs
  during the exact high-volatility days this strategy trades.
- **Multiple testing was addressed but not formally corrected.** The
  robustness sweep is presented as a full table specifically so a reader
  can see the false-positive pattern directly, rather than applying a
  Bonferroni/FDR correction that would just as clearly kill both
  "significant" cells — the qualitative conclusion doesn't depend on
  which approach is used.

## Conclusion

The evidence does not support the hypothesis that NIFTY reliably recovers
after a significant one-day fall, beyond what its ordinary upward drift
already explains. This is treated as a valid, informative negative
result — see `research_note.md` for the complete argument and
`AI_USAGE.md` for how AI tools were used in producing this analysis.
