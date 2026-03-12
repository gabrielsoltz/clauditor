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
- `--base-level` flag to enforce a minimum required scope

---

## Installation

```bash
pip install clauditor
```

Or from source:

```bash
git clone https://github.com/gabrielsoltz/clauditor
cd clauditor
python3.13 -m venv .venv
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

# Require settings to be enforced at project level or above
clauditor scan --base-level project

# Require enterprise-wide enforcement (managed only)
clauditor scan --base-level managed

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

Claude Code reads settings from multiple locations. Each location is a **scope**. Understanding scopes is key to understanding Clauditor's output.

### The four Claude Code scopes

| Column | Scope | File | Who it applies to |
|--------|-------|------|-------------------|
| `M` | `managed` | System path (platform-specific) | Everyone on the machine; deployed by IT |
| `L` | `local` | `.claude/settings.local.json` | You, in this repo only; **gitignored** |
| `P` | `project` | `.claude/settings.json` | All collaborators; **committed to git** |
| `U` | `user` | `~/.claude/settings.json` | You, across all projects |

### Scope precedence

When the same setting exists in multiple scopes, Claude Code applies **the highest-precedence scope**:

```
managed  >  local  >  project  >  user
(highest)                        (lowest)
```

`managed` is set by an administrator and cannot be overridden by anyone. `local` takes precedence over `project`, which means a developer can use `.claude/settings.local.json` to override what the team committed in `.claude/settings.json`.

### Repository scope (Clauditor extension)

| Column | Scope | What it checks |
|--------|-------|----------------|
| `R` | `repository` | VCS governance files: CODEOWNERS, workflow configs, etc. |

`repository` is **not a Claude Code scope** — it's Clauditor's own concept for checks that look at repository governance files rather than Claude Code JSON settings. It has no precedence relationship with the config scopes above.

---

## How Findings Work

### Per-scope icons in the output table

Each scope column shows one icon:

| Icon | Meaning |
|------|---------|
| `✔` | Setting is correctly configured at this scope |
| `✘` | Setting is present but has the wrong value |
| `↑` | Covered — a higher-precedence scope already passes, so this scope is irrelevant |
| `–` | Skipped — the settings file for this scope was not found or is empty |
| `·` | N/A — this check does not apply to this scope |

### How the effective (overall) status is decided

The **effective status** in the Status column is determined by the highest-precedence scope that is not skipped:

- If `managed=PASS` → effective is **PASS**, regardless of lower scopes. All lower scopes show `↑` (covered).
- If `managed=FAIL` → effective is **FAIL**, regardless of lower scopes. A wrong value at the top level locks everyone.
- If `managed=–, local=–, project=PASS` → effective is **PASS**, user shows `↑` (covered).
- If all config scopes are `–` (not configured anywhere) → effective is **FAIL**. A missing setting is not a passing setting.

### Scenario examples

**Scenario A — Enforced via managed settings (best)**

| M | L | P | U | Status |
|---|---|---|---|--------|
| ✔ | ↑ | ↑ | ↑ | ✔ PASS |

Setting is in managed. Everyone on the machine is protected. Lower scopes are irrelevant.

**Scenario B — Enforced via project settings (team-level)**

| M | L | P | U | Status |
|---|---|---|---|--------|
| – | – | ✔ | ↑ | ✔ PASS |

Setting is in `.claude/settings.json` (committed to git). All collaborators are protected. User scope is covered.

**Scenario C — Only the individual has it set**

| M | L | P | U | Status |
|---|---|---|---|--------|
| – | – | – | ✔ | ✔ PASS |

Setting is only in `~/.claude/settings.json`. Your own machine is protected, but teammates are not. This is PASS by default, but see `--base-level` below.

**Scenario D — Nobody has it set**

| M | L | P | U | Status |
|---|---|---|---|--------|
| – | – | – | – | ✘ FAIL |

The setting is not configured anywhere. This is always FAIL — a missing setting provides no protection.

**Scenario E — Wrong value at managed level**

| M | L | P | U | Status |
|---|---|---|---|--------|
| ✘ | – | ✔ | ✔ | ✘ FAIL |

Managed has the wrong value. Because managed takes highest precedence, it overrides the correct project/user values. Effective status is FAIL.

---

## `--base-level`: Enforcing a minimum scope

By default, Clauditor marks a check as PASS if the setting is correctly configured at **any** scope. However, you may want to require enforcement at a specific level.

```bash
# Require the setting to exist at project scope or above (for team-wide enforcement)
clauditor scan --base-level project

# Require enterprise-wide enforcement through managed settings only
clauditor scan --base-level managed
```

With `--base-level project`, **Scenario C above becomes FAIL** — the setting is only personal and doesn't protect the team.

| `--base-level` | What passes |
|----------------|-------------|
| `user` (default) | Any scope: user, project, local, or managed |
| `project` | Must be in project, local, or managed (not just user) |
| `local` | Must be in local or managed (not just project/user) |
| `managed` | Only managed qualifies |

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
| CC002 | Disable Bypass Permissions Mode | CRITICAL | user, project, local, managed | Unrestricted tool execution via --dangerously-skip-permissions |

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
├── aggregator.py       # Scope precedence + base_level logic
├── models/
│   ├── check.py        # Check, Scope, Severity, CheckType models
│   └── finding.py      # Finding, FindingStatus models
├── providers/
│   ├── base.py         # BaseProvider interface
│   ├── config_provider.py   # User, Project, Local, Managed providers
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
