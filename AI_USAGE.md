# AI Usage Note

## Tools Used

- **Claude** — primary tool, used throughout: research design, all Python
  code (data sourcing, validation, event detection, statistics,
  robustness testing, out-of-sample split, backtest), README, and
  research note.
- **ChatGPT** — brief use, mainly to cross-check terminology around
  hypothesis testing and confirm my understanding of a couple of
  statistical concepts (bootstrap vs. permutation test) while reading
  Claude's output.
- **Gemini** — minor, general background reading on NIFTY market
  structure and past crash events, not code.

## How I Used Them

I worked through the assignment task-by-task with Claude: gave it the
assignment PDF, then went step by step — source data, validate it, define
the event mathematically, build the detection engine, run statistical
tests, sweep thresholds for robustness, split out-of-sample, then a
simple backtest. I ran every script myself locally and pasted the actual
terminal output back so the next step was built on real numbers, not
assumed ones.

## My Own Decisions

- Chose to build this as a set of small, config-driven scripts
  (`config.py` holding every parameter) rather than a notebook, so I
  could rerun with different thresholds without touching logic — this was
  a direct requirement of the brief and I made sure the final code
  actually satisfied it, not just claimed to.
- When Claude suggested building an interactive Streamlit dashboard on
  top of this, I asked for it — Claude pushed back, pointing out the
  brief explicitly says not to build an elaborate UI and that it doesn't
  map to any rubric category. I agreed and dropped the idea; better to
  spend that time on the write-up.
- Decided what goes in `.gitignore` (kept `data/` and `results/` tracked
  for reproducibility, excluded `__pycache__`, venv, and my scratch
  `exps/` folder).
- Made the final call on repo structure and which files go where.

## Suggestions I Changed or Disagreed With

- The Streamlit dashboard idea above — my initial instinct, changed after
  hearing the rubric argument against it.
- Pushed to keep the AI-generated recovery-rate framing honest: an early
  draft of my own thinking treated a positive mean forward return as
  "recovery," but Claude's suggested distinction between *statistical*
  recovery (mean return > 0) and *practical* recovery (price actually
  climbs back to its pre-fall level) was better and is what's in the
  final research note — it's what exposed that the headline-looking
  numbers were mostly just NIFTY's normal upward drift.

## Incorrect AI Suggestions I Identified

- The first version of `event_engine.py` crashed with a pandas dtype
  error (a boolean column couldn't hold `NaN` for events too close to the
  end of the data). This was an AI-generated bug — I ran the script, hit
  the traceback, and it got fixed (nullable boolean dtype) before I
  re-ran it. Small, but a reminder to actually run everything rather than
  trust code on sight.
- The initial backtest total-return number (+34.5%) looked like a decent
  result on its own; I flagged that it needed a buy-and-hold comparison
  for context before it went in the README, since without it the number
  is easy to misread as evidence of a working strategy.

## What I Learned

- How multiple testing produces false positives in practice, not just in
  theory — the threshold sweep genuinely produced two "significant"
  cells that don't hold up once you look at neighboring thresholds.
- Why out-of-sample validation matters: the sign of the effect flipped
  completely between the research and OOS periods, which is a much more
  convincing falsification than any single p-value.
- The gap between a statistically framed "recovery" and an actual
  practical recovery to pre-fall price levels — and how easy it would be
  to accidentally oversell the former as the latter.
