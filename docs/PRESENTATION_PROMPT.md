[EN](PRESENTATION_PROMPT.md) | [RU](PRESENTATION_PROMPT.ru.md)

# Prompt for an external PPTX tool

Copy the prompt below into the presentation tool. Provide the repository's `README.md`, `docs/ARCHITECTURE.md`, `docs/COT_RELEASE_EVIDENCE.md`, `docs/SYNTHETIC_DEMO.md`, and `openspec/specs/capstone/spec.md` as source material if the tool accepts files.

> Create an English-language, 16:9 PowerPoint deck for an individual defense of the Stock Market Analytics Zoomcamp capstone. Use 9–10 concise slides, clear charts/diagrams, readable labels, restrained financial-research styling, and speaker notes with a short defense script. Audience: course reviewers and data practitioners. Deliver an editable `.pptx`.
>
> Project: investigate whether CFTC futures positioning, price history and cross-market signals can help estimate five-trading-session returns of GLD and SLV. These ETFs are the only target/traded assets. BTC-USD, SOL-USD, ETH-USD, ZEC-USD, NVDA, S&P 500, Nasdaq and Dow are contextual predictors, not targets. FRED is deferred until release timestamps and vintage data can be handled reliably.
>
> Keep the current evidence status explicit: the software workflow and deterministic tests exist, but no complete experiment on real market data or verified real-data performance results have been produced. Four COT release records have conservative historical availability cutoffs and are insufficient for the planned experiment. Source access has recently failed DNS checks. Do not invent results, sample coverage, performance, provider terms, project users, peer reviews, deployments or course acceptance. Leave real-data metrics blank or label them “not yet measured.”
>
> The project uses signal time at the actual NYSE close (including early closes), entry at the next session open, and exit after five held trading sessions. COT features are eligible only after evidenced public availability; unknown publication periods are excluded. Completed crypto UTC-day bars and the ETF exchange calendar are respected. Chronological train/validation/test splits purge overlapping label intervals; model and threshold selection use validation, and the holdout is not used for selection. Simulations include two-sided costs and a same-period buy-and-hold benchmark; the fixed-notional vectorized strategy is an approximation, while the event simulation models cash constraints.
>
> Suggested slide sequence:
> 1. Title, research question, researcher and current evidence-status banner.
> 2. Why GLD/SLV and what makes this study different from the course's baseline asset setup.
> 3. Source universe and pipeline architecture, marking unavailable/optional sources accurately.
> 4. Point-in-time timeline: COT publication, NYSE-close signal, next-open entry, five-session exit, and crypto cutoff.
> 5. Feature table examples and leakage controls; distinguish actual code features from unverified data coverage.
> 6. Chronological experiment design: purged splits, baseline, Ridge/tree/forest candidates, validation-only selection.
> 7. Trading rules, sizing, transaction costs, benchmark and the two simulation approaches.
> 8. Evidence and results: clearly state that real-data results are not yet available. If showing the synthetic demo, label every chart and slide “synthetic software demonstration only; not market evidence or strategy performance.”
> 9. Limitations: COT historical publication evidence, provider revisions, missing data, small fixed universe, survivorship/selection bias, costs, overfitting and no guarantee of future returns.
> 10. Reproduction commands, next steps, and a short defense walkthrough.
>
> Use only facts supported by supplied project files. Put a compact source citation on every slide that contains a sourced claim; cite the official course rubric and primary CFTC/provider documentation only when these are in the supplied materials. Never imply a profitable strategy or benchmark outperformance. Prefer a diagram of the pipeline and a point-in-time timeline over decorative financial imagery. Make synthetic figures visually distinct from any real-data evidence and include a visible disclaimer wherever they appear.
