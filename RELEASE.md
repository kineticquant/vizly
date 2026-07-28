# Releasing vizly (from GitHub Actions)

Publish **from GitHub**, not from your laptop. The [Release workflow](.github/workflows/release.yml) builds the sdist/wheel on a version tag and uploads via **PyPI Trusted Publishing** (OIDC). No `twine upload` and no long-lived API tokens required.

## One-time setup (Trusted Publishing)

### 1. GitHub Environments

In the repo **Settings → Environments**, create:

- `pypi`
- `testpypi` (optional dry-run)

You can add protection rules (required reviewers) on `pypi` if you want a human gate before production publish.

### 2. PyPI project → Publishing

On [pypi.org](https://pypi.org) (you already reserved `vizly`):

1. Open the project → **Settings → Publishing**
2. **Add a new pending publisher** (GitHub):
   - Owner: `kineticquant`
   - Repository: `vizly`
   - Workflow name: `release.yml`
   - Environment name: `pypi`

Do the same on [test.pypi.org](https://test.pypi.org) with environment `testpypi` if you want a dry-run lane.

### 3. Enable publish with repo variables

**Settings → Secrets and variables → Actions → Variables:**

| Variable | Value | Effect |
|----------|-------|--------|
| `ENABLE_TESTPYPI_PUBLISH` | `true` | Tag/dispatch may upload to TestPyPI |
| `ENABLE_PYPI_PUBLISH` | `true` | Tag/dispatch may upload to PyPI |

Leave them unset/`false` until the pending publisher is configured — the workflow will still **build + twine check** on every `v*` tag.

## Each release

1. Bump `version` in `pyproject.toml` and `src/vizly/_version.py` (keep in sync).
2. Update [CHANGELOG.md](CHANGELOG.md) (pin ECharts asset versions in the notes).
3. Merge to `main`.
4. Tag and push:

```bash
git tag v0.1.0
git push origin v0.1.0
```

That triggers **Release**: build → (optional) TestPyPI → (optional) PyPI.

Or: **Actions → Release → Run workflow**.

## Local verify (optional, no upload)

Full runbook: **[TESTING.md](TESTING.md)**.

```bash
pip install -e ".[dev]"
ruff check src/vizly tests
coverage run --source=vizly -m pytest -q -m "not browser"
coverage report --include='*/vizly/theme/*,*/vizly/data.py,*/vizly/base.py,*/vizly/api.py' --fail-under=70
python -m build
twine check dist/*
```

### Sample / golden charts (Level 2)

```bash
python -m pytest -m samples -v
python scripts/update_sample_goldens.py   # after intentional option/theme changes
```

### Browser validation (Level 3 + local review)

```bash
pip install -e ".[dev,browser]"
python -m playwright install chromium
python -m pytest -m browser -v                              # headless hero set
python scripts/validate_samples_browser.py --gallery        # visible full matrix
```

## CI vs Release

| Workflow | When | What |
|----------|------|------|
| [ci.yml](.github/workflows/ci.yml) | Push/PR to `main` | Lint, Level 1+2 tests, coverage, build; uploads sample HTML |
| [browser.yml](.github/workflows/browser.yml) | Weekly / `v*` tag / manual | Level 3 Playwright hero smoke |
| [release.yml](.github/workflows/release.yml) | `v*` tag or manual | Build artifacts + publish if enabled |

## Why not publish from the repo checkout on your PC?

You can, but Actions + Trusted Publishing is safer: credentials never live on a laptop, publishes are auditable in Actions logs, and environment protection can require approval.
