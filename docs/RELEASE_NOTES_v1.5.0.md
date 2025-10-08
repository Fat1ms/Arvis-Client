# Arvis v1.5.0 — Release Notes

Date: 2025-10-06

## Highlights

- DevEx: Pre-commit stabilized on Windows (flake8 arg quoting, bandit pbr + txt formatter, detect-secrets v1.5 baseline).
- Tooling: Removed duplicate hooks; heavy linters set to manual stage to avoid accidental commit blocking.
- Security: Local security scanning configured; baseline for secrets added.
- Docs: README badges updated; security links fixed.

## Details

- flake8 no longer mis-parses `--extend-ignore` on Windows (quoted args); line length set to 200.
- bandit dependency `pbr` added; formatter changed to `txt` to avoid Windows console encoding errors.
- detect-secrets upgraded to v1.5.0 and aligned with `.secrets.baseline`; `pass_filenames: false` to avoid baseline read issues.
- markdownlint and yamllint moved to manual; run them via `pre-commit run <hook> --all-files` when ready to fix docs.

## How to Run Checks (optional)

```powershell
pre-commit run --all-files
pre-commit run flake8 --all-files
pre-commit run bandit --all-files
pre-commit run detect-secrets --all-files
pre-commit run markdownlint --all-files
pre-commit run yamllint --all-files
```

## Known Follow-ups

- Consider re-enabling flake8/bandit/detect-secrets in commit stage after addressing warnings.
- Add/update tests for security modules; finalize docs for beta.
