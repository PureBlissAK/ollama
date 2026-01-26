PMO: Issues #24–#30 — Implementation Summary

Summary
-------
This release contains the PMO (Project Management Office) feature set implemented under `ollama/pmo/`. It addresses issues #24–#30 and includes unit tests, CI fixes, and documentation.

Key changes
-----------
- New package: `ollama/pmo/` with modules:
  - `agent.py`, `remediation.py`, `scheduler.py`, `drift_predictor.py`, `audit.py`, `classifier.py`, `analyzer.py`, and tests under `tests/unit/pmo/`.
- Tests: PMO unit tests pass locally: 132 passed, 2 skipped.
- Robustness: ensured `.pmo` artifacts are created on init, remediation audit/history logging, non-zero duration measurement, improved rollback handling for ad-hoc rollback_data, and classifier scoring adjustments.
- CI: Opened a CI-fix PR to ensure dev extras are installed in CI to provide runtime/test dependencies.

Files of interest
-----------------
- `ollama/pmo/remediation.py` — remediation engine, fixes, rollback, audit logging
- `ollama/pmo/scheduler.py` — scheduled tasks and history logging
- `tests/unit/pmo/` — unit tests for PMO features

Validation performed
--------------------
- Local PMO unit tests: `pytest -c /dev/null tests/unit/pmo` → 132 passed, 2 skipped
- Targeted fix: `tests/unit/pmo/test_remediation.py::TestRemediationEngine::test_rollback_fix` → passed

Next steps
----------
- Wait for CI to run on branch `feature/issue-24-predictive`.
- On CI green: merge PR `chore(pmo): merge issue-24-predictive` (PR #39), update issues #24–#30 with links to PR and release notes, mark Epic #18 complete, and close issues.

Notes
-----
- Some repo-wide checks (mypy, ruff, integration tests) require dev dependencies and are expected to run in CI which installs dev extras.
- A prepared issue-update script is included at `scripts/post_issue_updates.sh` to help post comments via `gh` CLI or GitHub API once CI passes.
