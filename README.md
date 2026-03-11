# Clauditor

**Security configuration scanner for Claude Code.**

Clauditor audits your Claude Code settings and repository configuration to detect security misconfigurations.

---

## Features

- Scans all Claude Code configuration scopes: **user**, **project**, **local**, and **managed**
- Checks **repository-level files** (CODEOWNERS, CLAUDE.md, etc.)
- Checks are defined as **YAML files** — easy to read, extend, and contribute
- Each check maps to a concrete **threat**, **severity**, and **remediation**
- Scan a **local path**, a **remote git URL**, or just the current directory
- Rich terminal output with optional verbose remediation steps
- CI-friendly `--exit-code` flag

---

## Installation

```bash
pip install clauditor
```

Or from source:

```bash
git clone https://github.com/gabrielsoltz/clauditor
cd clauditor
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Usage

```bash
# Scan current directory (project + user scope settings)
clauditor scan

# Scan a specific local repository
clauditor scan --path /path/to/repo

# Clone and scan a remote repository
clauditor scan --url https://github.com/org/repo

# Scan only user scope (~/.claude/settings.json)
clauditor scan --user-only

# Filter by severity
clauditor scan --severity CRITICAL,HIGH

# Filter by scope
clauditor scan --scope user,project

# Show remediation steps for failed checks
clauditor scan -v

# Exit with code 1 if any failures found (for CI)
clauditor scan --exit-code

# List all available checks
clauditor list-checks
```

---

## Configuration Scopes

| Scope | File | Description |
|-------|------|-------------|
| `managed` | System path (platform-specific) | All users on the machine; deployed by IT. **Highest precedence, cannot be overridden.** |
| `local` | `.claude/settings.local.json` | You, in this repository only; not shared with team (gitignored) |
| `project` | `.claude/settings.json` | All collaborators on this repository; shared with team (committed to git) |
| `user` | `~/.claude/settings.json` | You, across all projects; not shared with team |
| `repository` | Repo root files | Repository files like CODEOWNERS, CLAUDE.md *(Clauditor extension, not a Claude Code scope)* |

---

## Check Format

Checks live in the `checks/` directory as YAML files. Example structure:

```yaml
id: CC001
name: CODEOWNERS Enforcement for Claude Code Paths
description: >
  Ensures that /.claude/ and /CLAUDE.md have CODEOWNERS entries
  requiring security team review.

scope:
  - repository

severity: HIGH  # CRITICAL | HIGH | MEDIUM | LOW | INFO

threat: >
  Without CODEOWNERS enforcement, contributors can silently modify
  Claude Code settings, hooks, or instructions without security review...

category: access_control

check_type: file_content  # config_value | file_content | file_exists

check_config:
  search_paths:
    - CODEOWNERS
    - .github/CODEOWNERS
  required_entries:
    - pattern: "/.claude/"
      owner: "@security-team"
    - pattern: "/CLAUDE.md"
      owner: "@security-team"

remediation: >
  Add to CODEOWNERS:
    /.claude/ @security-team
    /CLAUDE.md @security-team

fix_available: true

references:
  - https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
  - https://code.claude.com/docs/en/settings
```

### Check Types

| `check_type` | `check_config` keys | Description |
|---|---|---|
| `config_value` | `key`, `expected_value` | Verifies a key/value in a JSON settings file |
| `file_content` | `search_paths`, `required_entries` | Verifies required lines exist in a file |
| `file_exists` | `paths`, `any_of` | Verifies file(s) exist in the repository |

---

## Built-in Checks

| ID | Name | Severity | Scope | Threat Mitigated |
|----|------|----------|-------|-----------------|
| CC001 | CODEOWNERS Enforcement for Claude Code Paths | HIGH | repository | Supply chain attacks via unreviewed config changes |
| CC002 | Disable Bypass Permissions Mode | CRITICAL | user, project, managed | Unrestricted tool execution via --dangerously-skip-permissions |

---

## Adding a Custom Check

1. Create a new YAML file in `checks/` following the format above.
2. Assign the next available `CC###` ID.
3. Run `clauditor list-checks` to verify it loads correctly.
4. Run `clauditor scan` to see results.

No code changes required.

---

## Architecture

```
clauditor/
├── cli.py              # Typer CLI entry point
├── scanner.py          # Orchestrates checks against providers
├── loader.py           # YAML check loader with Pydantic validation
├── models/
│   ├── check.py        # Check, Scope, Severity, CheckType models
│   └── finding.py      # Finding, FindingStatus models
├── providers/
│   ├── base.py         # BaseProvider interface
│   ├── config_provider.py   # Global, Project, Local, Managed providers
│   └── repository_provider.py  # Repository file provider + git clone
├── checkers/
│   ├── config_value.py  # Logic for config_value checks
│   ├── file_content.py  # Logic for file_content checks
│   └── file_exists.py   # Logic for file_exists checks
└── output/
    └── console.py       # Rich terminal output

checks/                  # YAML check definitions
```

---

## License

Apache 2.0
