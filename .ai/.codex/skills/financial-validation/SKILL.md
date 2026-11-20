---
name: financial-validation
description: Use when building or reviewing time-series features, predictive splits, or financial simulations.
---

# Financial validation

1. Identify the precise signal cutoff, exchange calendar, execution price/time and target start/end. Use only completed observations, including crypto bars, available at the cutoff.
2. Split chronologically. Purge labels whose intervals overlap the next split; fit preprocessing on training only, select model and trading parameters on validation only and evaluate holdout after selection.
3. Check position sizing, available cash, overlapping holdings, price adjustments, commissions and slippage against independently calculated examples. Align the benchmark period and cost assumptions.
4. Report actual dates, sample sizes, metrics, gaps and untested assumptions. Do not infer future returns from historical results.
