[EN](index.md) | [RU](index.ru.md)

# Documentation

This directory contains project documentation for users and reviewers. The root [README](../README.md) is the short entry point. English is primary; main human-facing documents have a Russian companion using `.ru.` in the filename.

The structure follows a lightweight Diátaxis approach: start with tasks, then consult explanations, reference material and project evidence. Files remain in place so existing links keep working.

## Start here

- **Run the project:** [Local research runbook](RUNBOOK.md) covers setup, data retrieval, offline replay and troubleshooting.
- **See the workflow:** [Synthetic demo](SYNTHETIC_DEMO.md) runs the pipeline on clearly labeled fictional inputs.
- **Understand the design:** [Architecture and data flow](ARCHITECTURE.md) explains sources, timing and evaluation.

## Reference and evidence

- [Command reference](COMMANDS.md) for Make and Just operations.
- [COT publication evidence](COT_RELEASE_EVIDENCE.md) for report availability and coverage limits.
- [Feature dictionary](FEATURE_DICTIONARY.md) maps source, availability, transformations and model roles to course modules.
- [Market EDA and model comparisons](EDA_FINDINGS.md) reports local price diagnostics, the COT table and full-COT validation comparison.
- [Course criteria status](COURSE_CRITERIA_STATUS.md) for rubric evidence and open obligations.
- [Changelog](CHANGELOG.md) for dated, evidence-based project changes.
- [Periodic commit and push guide](PERIODIC_COMMIT_PUSH.md) for the optional macOS schedule.

## Research and presentation

- [Independent final QA](FINAL_QA.md): frozen experiment audit, clean installation/notebook results, provider terms and course follow-up.

- [Workflow and MLOps stack assessment](research/workflow-and-ml-stack.md).
- [Proposed orchestration ADR](adr/0001-orchestration-and-experiment-management.md).
- [Presentation prompt](PRESENTATION_PROMPT.md) for an external slide-authoring tool.

Russian mirrors are available for the README, runbook, demo, architecture, commands, COT evidence, feature dictionary, EDA findings, final QA, course criteria, changelog, periodic operations, presentation prompt, this index, and the ADR/research pages.

The full experiment is reproducible, but its holdout results are negative and do not establish future profitability. See the README for current evidence and [`.ai/`](../.ai/IMPLEMENTATION_PLAN.md) for plans, backlog and agent operations.
