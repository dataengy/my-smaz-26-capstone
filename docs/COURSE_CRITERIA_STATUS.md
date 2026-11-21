# Course criteria coverage

**Checked:** 2026-11-21 against the [official course project rubric](https://raw.githubusercontent.com/DataTalksClub/stock-markets-analytics-zoomcamp/main/projects/README.md). The source remains reachable and unchanged in the criteria relevant here: six bold minimum-score gates, an individual presentation, three peer evaluations for project points, and the listed attempt-one deadline of 2026-11-20 23:59:59 Dublin time.

[Русская версия](COURSE_CRITERIA_STATUS.ru.md).

This is a dated summary of evidence in this workspace, not a predicted score or reviewer decision. **Partial** means an artifact or code path exists but required course evidence or acceptance is not established. The [full criterion-by-criterion matrix](../openspec/specs/capstone/spec.md#course-acceptance-evidence-matrix) has the evidence links and reasons. Refresh this summary whenever the `capstone-verification` skill is run.

## Minimum-score criteria

The rubric bolds six criteria as the minimum-score gate. None is verified as a completed course outcome:

| Required criterion | Status | Current evidence |
|---|---|---|
| Brief problem description in README | Partial | README describes the GLD/SLV forecasting problem; reviewer acceptance is unknown. |
| Lecture data sources and features | Partial | [Feature dictionary](FEATURE_DICTIONARY.md) maps sources/features to official Modules 1–5; a full COT-inclusive real-data experiment is now frozen, but course acceptance remains unverified. The dictionary currently describes five derived examples; the 20+ feature criterion is not met. |
| Combined dataframe and defined feature sets | Partial | The latest frozen experiment used 1,916 modeled rows, 1,906 labeled rows and 211 release dates after point-in-time filtering; see [full-run report](FULL_RUN.md). Rubric acceptance remains reviewer-dependent. |
| DecisionTree or RandomForest | Partial | The canonical COT-inclusive comparison evaluates DecisionTree and RandomForest candidates against the mean baseline and selects mean by validation MAE; two current-code calculations match 20 numerical output hashes. Earlier unprovenanced root outputs were excluded and refreshed. See the [full-run report](FULL_RUN.md). Reviewer acceptance remains unverified. |
| Vector simulation and approximate capital returns | Partial | The frozen experiment reports both the vectorized approximation and cash-constrained event simulation with negative net holdout results; rubric acceptance remains reviewer-dependent. |
| Exported scripts and end-to-end notebook | Partial | Scripts and notebook exist; offline setup and workflow notebook cells completed from `notebooks/`; full kernel launch and a clean uncached install remain unverified (see [final QA](FINAL_QA.md)). |

**Gate coverage:** 0 course outcomes verified, 6 partial, 0 open. Project implementation evidence has improved; the “verified” course status still depends on rubric/reviewer acceptance. Partial implementation does not establish earned points. Provider reuse/redistribution rights remain unconfirmed, and a clean uncached installation and full notebook-kernel launch remain unverified; see [independent QA](FINAL_QA.md).

The code-level source → availability → transformation → model-role inventory, five representative derived features and module mapping are in the [feature dictionary](FEATURE_DICTIONARY.md). Full-history market EDA and the 1,916-row full-COT experiment are documented in [EDA findings](EDA_FINDINGS.md) and [full-run report](FULL_RUN.md). Incremental COT value requires an appropriate ablation experiment; no evidence here establishes future profitability.

## Overall rubric evidence

| Status | Criteria | Meaning |
|---|---:|---|
| Verified | 0 | Complete outcome supported by observed evidence. |
| Partial | 20 | Some implementation evidence exists; course outcome remains unverified. |
| Open | 16 | Required artifact, experiment, outcome or reviewer judgment is missing. |
| Blocked | 0 | None separately classified in the rubric matrix; practical source/data blockers are described there. |
| Deferred | 0 | None; optional bonus criteria are currently open. |
| **Total** | **36** | Course rubric criteria, including bonus criteria. |

The project now has a frozen COT-inclusive study, purged holdout, two cost-aware simulations and matching replay; provider-vintage and legal-rights limitations remain. Synthetic demos and software tests are not finance evidence.

## Separate course obligations

- **Submission:** the official page lists the 2026 attempt-one deadline as 2026-11-20 23:59:59 Dublin time; it has passed. No later attempt or project submission evidence is established here.
- **Individual presentation:** required by the rubric; completion is not evidenced.
- **Three peer evaluations:** the official page says to evaluate three peer projects to obtain project points; completion is not evidenced.

The official rubric page was reachable at the checked URL on the date above. Recheck it before submission because deadlines and course rules can change.
