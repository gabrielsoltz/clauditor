# Clauditor — Roadmap / Ideas

## Pending Ideas

### CI/CD Integration
- **Pre-commit hook** — run `clauditor scan --exit-code` as a pre-commit hook so misconfigurations are caught before commit
- **GitHub Actions workflow** — publish a reusable workflow that teams can drop into their repo to run Clauditor on every PR

### Output Formats
- **JSON export** — `clauditor scan --output-format json` to export findings as structured JSON (useful for programmatic processing and dashboards)
- **SARIF output** — export results in SARIF format for upload to GitHub Code Scanning, surfacing findings as native security alerts in the repository

### Checks Expansion
- **Hooks validation** — inspect hook configurations (`.claude/settings.json` `hooks` key) for dangerous patterns: arbitrary shell commands, network calls, or missing approval requirements
- **CLAUDE.md security checks** — validate that `CLAUDE.md` doesn't contain insecure instructions (e.g. "skip permissions", "allow all tools", "do not ask for confirmation")

### Remediation
- **Auto-remediate mode** — `clauditor fix` command that applies the generated settings file directly to the correct path for the chosen scope, with a confirmation prompt before writing

### Analysis
- **Scan comparison / diff** — compare two scan results (e.g. before and after a change) to surface what improved or regressed, useful for tracking security posture over time
