[EN](PERIODIC_COMMIT_PUSH.md) | [RU](PERIODIC_COMMIT_PUSH.ru.md)

# Periodic local commit and push

The optional macOS LaunchAgent in `scripts/periodic_commit_push.py` checks this checkout on a schedule. Install it after `main` tracks `origin/main`:

```sh
python3 scripts/periodic_commit_push.py install --interval-minutes 30 --quiet-minutes 10
```

The defaults check every 30 minutes and require all changed files to be quiet for 10 minutes. The agent only operates on `main` with the expected GitHub origin and a clean index. It waits while any project object lock is held, skips protected paths and files over 1 MiB, runs the configured prek hooks, stages eligible project changes, creates a timestamped commit, and pushes to `origin/main`. It never force-pushes. If the push fails, the local commit remains for inspection.

The scheduler is opt-in and is installed in the current user's `~/Library/LaunchAgents`. It does not run at login; its first check occurs on the configured interval. Logs go to the ignored `.run/periodic-commit-push.log`. GitHub Actions remains responsible for the test suite after a push; the scheduled task does not run tests.

Manage the LaunchAgent:

```sh
python3 scripts/periodic_commit_push.py uninstall
```

Run one cycle manually:

```sh
python3 scripts/periodic_commit_push.py run
```

The automation skips environment files, local data, caches, credentials, key/certificate files, databases, and large files. It does not inspect arbitrary file contents for secrets. Review `.gitignore` and keep secrets out of the checkout.
