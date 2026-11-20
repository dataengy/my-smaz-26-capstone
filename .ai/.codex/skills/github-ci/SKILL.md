---
name: github-ci
description: Add, troubleshoot, and maintain GitHub Actions workflows for this capstone repository.
---

# GitHub Actions for this project

- The CI contract lives in `.github/workflows/ci.yml`: run prek checks and the locked Python test suite for pushes to `main`, pull requests, and manual dispatch.
- Keep workflow permissions minimal (`contents: read` for checks), pin third-party actions to reviewed full commit SHAs with version comments, and use `uv.lock` for dependency resolution.
- CI must not download market data, require secrets, or describe fixture tests as a successful real-data experiment. The E2E tests remain opt-in unless explicitly configured.
- Preserve the `uv sync --locked --extra test` installation path and report skipped checks honestly.
- Validate workflow YAML and inspect changed files before handoff. A locally valid workflow is not evidence that GitHub Actions ran; verify run status before reporting CI success.
- Coordinate workflow changes with the GitHub Actions file lock and keep the handoff specific to the changed jobs, commands, and actual results.
