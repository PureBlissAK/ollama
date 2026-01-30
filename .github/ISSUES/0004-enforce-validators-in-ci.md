---
title: "Enforce folder-structure and PMO validation in CI"
labels: [ci, infra, pmo-compliance]
assignees: [kushin77, team-devops]
---

## Summary

Add steps to CI to run `scripts/validate_folder_structure.py --strict` and `scripts/pmo/validate-pmo-metadata.sh` to prevent regressions and ensure repository remains Landing Zone-compliant.

## Proposed CI changes

- Add a job `validate-landing-zone` to `.github/workflows/full-ci-cd.yml` that runs on push and PRs to `main` and `feature/*`:
  - `python3 scripts/validate_folder_structure.py --strict`
  - `bash scripts/pmo/validate-pmo-metadata.sh`
  - `pytest -q` (optional for safety)

## Acceptance criteria

- CI fails when folder structure or PMO metadata validations fail
- Documentation updated describing the CI checks

## Notes

Add caching for Python dependencies if needed and ensure job runs in a matrix where necessary.

---
Status: Completed (workflow added)
Resolution: Added `.github/workflows/validate-landing-zone.yml` to run PMO and folder-structure validators plus a detect-secrets scan. Further tuning may be required for CI runner tooling. (2026-01-30)
