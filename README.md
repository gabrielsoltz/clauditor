<p align="center">
  <img src="logo.png" alt="Clauditor" width="200">
</p>

# Clauditor

**Security configuration scanner for Claude Code.**

[![Tests](https://github.com/gabrielsoltz/clauditor/actions/workflows/test.yml/badge.svg)](https://github.com/gabrielsoltz/clauditor/actions/workflows/test.yml)
[![Security](https://github.com/gabrielsoltz/clauditor/actions/workflows/security.yml/badge.svg)](https://github.com/gabrielsoltz/clauditor/actions/workflows/security.yml)
[![Lint](https://github.com/gabrielsoltz/clauditor/actions/workflows/lint.yml/badge.svg)](https://github.com/gabrielsoltz/clauditor/actions/workflows/lint.yml)
[![PyPI](https://img.shields.io/pypi/v/clauditor)](https://pypi.org/project/clauditor/)
[![Python](https://img.shields.io/pypi/pyversions/clauditor)](https://pypi.org/project/clauditor/)
[![License](https://img.shields.io/github/license/gabrielsoltz/clauditor)](LICENSE)

Clauditor audits your Claude Code settings and repository configuration to detect security misconfigurations.

---

## Table of Contents

- [Features](#features)
- [Why This Matters — For Developers](#why-this-matters--for-developers)
- [Why This Matters — For Security Teams](#why-this-matters--for-security-teams)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration Scopes](#configuration-scopes)
- [How Findings Work](#how-findings-work)
- [Enforcing a Minimum Scope](#enforcing-a-minimum-scope)
- [Check Format](#check-format)
- [Generating a Settings File](#generating-a-settings-file)
- [Adding a Custom Check](#adding-a-custom-check)
- [Architecture](#architecture)
- [License](#license)

---

## Features

- Scans Claude Code configuration at every scope: **user**, **project**, **local**, and **managed**
- **50+ built-in security checks**, ready to use with no configuration — each with a severity rating, a documented attack scenario, step-by-step remediation, and external references
- Checks **repository-level files** (CODEOWNERS, CLAUDE.md, etc.)
- Checks are defined as **YAML files** — easy to read, extend, and contribute
- Each check maps to a concrete **threat**, **severity**, and **remediation**
- Scan a **local path**, a **remote git URL**, or just the current directory
- **Generate a hardened settings file** with `clauditor generate`: produces a ready-to-deploy JSON file that remediates all applicable checks for your chosen scope (user, project, or managed)
- Rich terminal output with optional verbose remediation steps
- CI-friendly `--exit-code` flag for pipeline integration
- `--base-level` flag to enforce a minimum required scope (e.g. require managed-level enforcement)

<p align="center">
  👉 <strong><a href="https://gabrielsoltz.github.io/clauditor/">Browse all checks →</a></strong>
</p>

---

## Why This Matters — For Developers

Claude Code has direct access to your shell, your files, and your network. That power is what makes it useful — and what makes its configuration worth protecting.

**Someone else's settings run on your machine.**
Claude Code project settings are committed to git and apply to everyone who works on the repository. Imagine you clone an open-source project to contribute a small fix. Unbeknownst to you, a maintainer (or an attacker who compromised a maintainer account) added a configuration that runs a custom script every time Claude Code starts a session. That script sends your API key to an external server. You never saw it happen. Clauditor checks for this class of risk before you start working.

**A poisoned doc can hijack your session.**
You ask Claude to summarize a README from a third-party library. That README contains hidden instructions — invisible to you, readable by Claude — telling it to exfiltrate the contents of your `~/.ssh` directory or run a reverse shell. Whether that attack succeeds depends entirely on what permissions Claude Code has. If your configuration allows unrestricted shell commands and unrestricted network access, the attack has everything it needs. If access is locked down, Claude simply can't comply. Clauditor tells you exactly how open your current permissions are.

**You might be running a credential harvester without knowing it.**
Some Claude Code settings let a repository define a helper script that runs to generate authentication tokens or refresh cloud credentials. If that setting is present in a project you cloned — pointing to a script inside the repo itself — you are executing untrusted code with access to your credentials on every session start. No prompt, no warning. Clauditor detects when these helpers are defined at the project level, where they should never be.

Clauditor scans how your Claude Code is configured in your machine and in any repositories you work with (locally or remotely).

---

## Why This Matters — For Security Teams

Claude Code is a new category of tool: an AI agent with persistent shell, filesystem, and network access that developers run continuously during their workday. It introduces attack surface that traditional security tooling doesn't cover.

**Project settings are a supply chain vector.** `.claude/settings.json` is committed to git. Any contributor with repository write access can modify Claude Code's behavior for everyone on the project — adding hooks that exfiltrate data, granting unrestricted `Bash` permissions, or redirecting telemetry to an external collector. This is a lateral movement path that bypasses most existing controls.

**Managed settings are your enforcement layer.** Claude Code supports a managed settings file deployed via MDM or configuration management. It takes the highest precedence and cannot be overridden by users or projects (if they don't have the necessary permissions). Without it, every developer's Claude Code instance runs with whatever settings they (or the project) have configured — which may be insecure defaults.

**You need visibility.** Claude Code supports OpenTelemetry export of session metadata, tool calls, bash commands, and token usage. Without explicitly configuring a telemetry pipeline in managed settings, you have no audit trail of how Claude Code is being used across your fleet.

**Compliance requires repeatability.** Clauditor produces machine-readable results and exits with a non-zero code on failures, making it suitable for CI pipelines, periodic audits, and compliance evidence collection.

---

## Installation

The recommended way to install Clauditor is with [pipx](https://pipx.pypa.io), which installs CLI tools in isolated environments and makes them available system-wide:

```bash
pipx install clauditor
```

Install pipx if you don't have it yet:

```bash
# macOS
brew install pipx && pipx ensurepath

# Linux / WSL
python3 -m pip install --user pipx && pipx ensurepath
```

**From source:**

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

# Filter by severity
clauditor scan --severity CRITICAL,HIGH

# Show remediation steps for failed checks
clauditor scan -v

# Exit with code 1 if any failures found (for CI)
clauditor scan --exit-code

# List all available checks
clauditor list-checks

# Generate a settings file (user scope by default)
clauditor generate

# Generate a managed settings file covering all checks
clauditor generate --scope managed -o managed-settings.json
```

---

## Configuration Scopes

Claude Code reads settings from multiple locations. Each location is a **scope**. Understanding scopes is key to understanding Clauditor's output.

See the [official Claude Code settings documentation](https://code.claude.com/docs/en/settings) for details.

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

**Scenario D — Nobody has it set**

| M | L | P | U | Status |
|---|---|---|---|--------|
| – | – | – | – | ✘ FAIL |

The setting is not configured anywhere. This is always FAIL — a missing setting provides no protection.

---

## Enforcing a Minimum Scope

By default, Clauditor marks a check as PASS if the setting is correctly configured at **any** scope. However, you may want to require enforcement at a specific level.

```bash
# Require the setting to exist at project scope or above (for team-wide enforcement)
clauditor scan --base-level project

# Require enterprise-wide enforcement through managed settings only
clauditor scan --base-level managed
```

With `--base-level project`, a setting that is only present in the user scope becomes FAIL — the setting is only personal and doesn't protect the team.

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
id: CC002
name: Disable Bypass Permissions Mode
description: >
  Ensures that the disableBypassPermissionsMode setting is explicitly set to
  "disable" across applicable Claude Code configuration scopes (user, project,
  local, managed). This prevents users from launching Claude Code with the
  --dangerously-skip-permissions flag, which bypasses all permission controls.

scope:
  - user
  - project
  - local
  - managed

severity: CRITICAL

threat: >
  When bypass permissions mode is not locked down, any user can run Claude Code
  with --dangerously-skip-permissions, which disables all tool permission prompts
  and approval gates. An attacker or careless developer can exploit this to allow
  Claude to execute arbitrary shell commands, read/write any file, make network
  requests, and perform other destructive actions without any human approval step.
  In CI/CD pipelines or shared environments, this can lead to complete
  compromise of the system, secret exfiltration, or supply chain attacks.

category: permissions

check_type: config_value

check_config:
  key: disableBypassPermissionsMode
  expected_value: "disable"

remediation: >
  Set disableBypassPermissionsMode to "disable" in the appropriate
  Claude Code settings file:

  For user scope enforcement (~/.claude/settings.json):
    {
      "disableBypassPermissionsMode": "disable"
    }

  For project-level enforcement (.claude/settings.json):
    {
      "disableBypassPermissionsMode": "disable"
    }

  For local-only enforcement (.claude/settings.local.json):
    {
      "disableBypassPermissionsMode": "disable"
    }

  For enterprise-wide enforcement, deploy via managed settings:
    {
      "disableBypassPermissionsMode": "disable"
    }

  The managed scope takes the highest precedence and cannot be overridden
  by users, making it the most effective enforcement point.

fix_available: true

references:
  - https://code.claude.com/docs/en/settings
```

### Check Types

| `check_type` | `check_config` keys | Description |
|---|---|---|
| `config_value` | `key`, `expected_value` | Verifies a key equals a specific value in a JSON settings file |
| `config_contains` | `key`, `required_values` | Verifies a list key contains all required values |
| `config_set` | `key` | Verifies a key is present and non-empty (any truthy value) |
| `config_absent` | `key` | Verifies a key is **not** present — used for settings that are dangerous when committed to shared scopes (e.g. credential helpers, telemetry endpoints) |
| `config_not_contains` | `key`, `forbidden_values` | Verifies a list key does **not** contain any of the forbidden values (e.g. overly broad permission grants) |
| `file_content` | `search_paths`, `required_entries` | Verifies required entries exist in a file; each entry needs a `pattern`, and an optional `owner` — if `owner` is omitted, any non-empty owner is accepted |
| `file_exists` | `paths`, `any_of` | Verifies file(s) exist in the repository |

---

## Generating a Settings File

`clauditor generate` produces a ready-to-deploy JSON settings file containing all the values needed to remediate the applicable checks.

```bash
clauditor generate                          # All checks → user settings
clauditor generate --scope managed         # Full managed settings file
clauditor generate --scope project         # Project-level (.claude/settings.json)
clauditor generate --severity CRITICAL     # Only critical checks
clauditor generate --checks CC002,CC010    # Specific checks only
clauditor generate --scope managed -o managed-settings.json
```

**Scope controls which checks are included:**

| `--scope` | Checks included |
|-----------|----------------|
| `user` (default) | user-scoped checks only |
| `project` | project + user checks |
| `local` | local + project + user checks |
| `managed` | All config checks: managed + local + project + user |

**What gets generated:**
- `config_value` checks → sets the key to its required value
- `config_contains` checks → builds/merges the required list entries (e.g. multiple checks writing to `permissions.deny` are merged automatically)
- `config_set` checks → **skipped** (e.g. `forceLoginOrgUUID` requires your org-specific UUID; reported separately)
- `config_absent` / `config_not_contains` checks → **skipped** (these flag things that should be removed, not added)
- `file_content` / `file_exists` checks → **skipped** (repository governance files, not settings values)

**Example output** (`clauditor generate --scope managed`):

```json
{
  "disableBypassPermissionsMode": "disable",
  "allowManagedPermissionRulesOnly": true,
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(**/.env)",
      "Read(secrets/**)",
      "Write(secrets/**)",
      "Read(**/credentials)",
      "Bash(curl:*)",
      "Bash(wget:*)"
    ]
  },
  "enableAllProjectMcpServers": false,
  "allowManagedHooksOnly": true,
  "forceLoginMethod": "claudeai",
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "denyWrite": ["/etc", "/usr", "~/.ssh", "~/.aws"],
      "denyRead": ["~/.ssh", "~/.aws/credentials", ".env", "**/.env"]
    }
  }
}
```

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
├── generator.py        # Settings file generator
├── models/
│   ├── check.py        # Check, Scope, Severity, CheckType models
│   └── finding.py      # Finding, FindingStatus models
├── providers/
│   ├── base.py         # BaseProvider interface
│   ├── config_provider.py   # User, Project, Local, Managed providers
│   └── repository_provider.py  # Repository file provider + git clone
├── checkers/
│   ├── config_value.py         # Logic for config_value checks
│   ├── config_contains.py      # Logic for config_contains checks
│   ├── config_set.py           # Logic for config_set checks
│   ├── config_absent.py        # Logic for config_absent checks
│   ├── config_not_contains.py  # Logic for config_not_contains checks
│   ├── file_content.py         # Logic for file_content checks
│   └── file_exists.py          # Logic for file_exists checks
└── output/
    └── console.py       # Rich terminal output

checks/                  # YAML check definitions
```

---

## License

Apache 2.0
