# Contributing to Clauditor

Thank you for your interest in contributing!

## Ways to Contribute

- **Add a new check** — the most impactful contribution
- **Improve an existing check** — better threat descriptions, remediation steps, or references
- **Report a bug** — open a GitHub issue with reproduction steps
- **Suggest an idea** — open a GitHub issue or check the [TODO](TODO.md) for planned work

## Adding a New Check

1. Pick the next available `CC###` ID from the [check list](README.md#built-in-checks)
2. Create a YAML file in `checks/` following the existing format
3. Run `clauditor list-checks` to verify it loads correctly
4. Run `clauditor scan` to see it in action
5. Open a PR with a short description of the threat being addressed

No code changes are required to add a check — just a YAML file.

## Check Format Reference

See the [Check Format](README.md#check-format) section in the README for the full schema and available `check_type` values.

## Development Setup

```bash
git clone https://github.com/gabrielsoltz/clauditor
cd clauditor
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Running Tests

```bash
pytest
```

## Code Style

This project uses `ruff` for linting and `mypy` for type checking. Both run automatically via pre-commit hooks. To run manually:

```bash
ruff check .
mypy clauditor/
```

## Pull Request Guidelines

- Keep PRs focused — one check or one fix per PR
- For new checks, include references to the threat source (CVE, research post, official docs)
- All CI checks must pass before merging
