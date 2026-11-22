---
name: smart-commit-and-push
description: Run validation, curate commits, verify tokens/scopes, push to upstream branch, and open CI page.
---

# smart-commit-and-push Skill

Validates repository state, audits artifacts, formats commit messages, verifies authentication and permission scopes, pushes to the upstream branch, and displays/opens the CI page.

## When to Use

- "smart-commit-and-push", "commit and push", "save and publish"
- After completing changes, features, bug fixes, or documentation updates ready for remote publication
- To ensure no broken code, conflict markers, temporary files, or unpermitted workflow diffs are pushed

## Workflow Phases

### Phase 0: Auth & Permission Pre-Flight

Before committing or pushing, verify authentication credentials for the active remote:

1. **Detect Remote Host**:
   ```bash
   REMOTE_URL="$(git config --get remote.origin.url)"
   ```
2. **GitHub Remotes**:
   - Verify `gh auth status`. Check active account and token scopes (`repo`, `workflow`, etc.).
   - **Workflow Scope Guard**: Check if any unpushed commit or staged change modifies `.github/workflows/*`:
     ```bash
     git diff --name-only origin/main..HEAD | grep -E '^\.github/workflows/' || true
     ```
   - If `.github/workflows/` is modified and the active GitHub token lacks the `workflow` scope, GitHub will reject the push (`refusing to allow an OAuth App to create or update workflow without workflow scope`).
   - Resolution:
     - Either prompt the user to grant `workflow` scope: `gh auth refresh -h github.com -s workflow`
     - Or restore `.github/workflows/` to match upstream if CI changes are not part of the current task.
3. **GitLab Remotes**:
   - Verify `glab auth status`. Refresh if expired.

### Phase 1: Working Tree Cleanliness & Artifact Audit

1. **Inspect Git Status**:
   - Verify current branch and ensure HEAD is not detached.
   - If in the middle of an interrupted rebase or merge, resolve or cleanly abort before new commits.
2. **Exclude Prohibited Artifacts**:
   - Ensure temporary SQLite databases (`*.db`), temporary runner directories (e.g. `.tmp_dagster*`), downloaded caches, virtualenvs, and secrets are not staged.
   - Ensure `.gitignore` covers runtime-generated directories.
3. **Check for Unresolved Conflicts**:
   - Confirm no conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) exist in tracked files:
     ```bash
     git grep -E '^(<<<<<<<|=======|>>>>>>>)' || true
     ```

### Phase 2: Test & Code Quality Validation

1. Run the project verification suite before committing:
   - For this repo: `make test` or `just verify` (or `make verify-fast`).
   - Never push code that breaks unit or integration tests unless explicitly overridden by user.
2. Confirm documentation and translation parity where required.

### Phase 3: Curate Clean Commits

1. **Avoid Generic Messages**:
   - Do not leave raw "save.." commit messages in unpushed history.
   - Use Conventional Commits (`feat(...)`, `fix(...)`, `docs(...)`, `chore(...)`, `test(...)`).
2. **History Rewriting (Unpushed Only)**:
   - Squash redundant work-in-progress "save.." commits before pushing to keep history readable and clean.
   - Never rewrite published remote history.

### Phase 4: Push to Upstream

1. Push to remote tracking branch:
   ```bash
   git push origin <branch>
   ```
2. Verify remote ref is updated (`git ls-remote` or `git log -1 origin/<branch>`).

### Phase 5: Surface CI Status

Display the direct link to the CI / Actions dashboard:
- GitHub: `https://github.com/<owner>/<repo>/actions`
- GitLab: `<repo-url>/-/pipelines` or `/-/jobs`
