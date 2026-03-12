"""Settings file generator.

Builds a Claude Code JSON settings dict from check definitions,
containing all the values needed to pass the selected checks.

Scope inclusion rules (mirrors scope precedence, in reverse):
    managed  → includes checks applicable to: managed, local, project, user
    local    → includes checks applicable to: local, project, user
    project  → includes checks applicable to: project, user
    user     → includes checks applicable to: user only

check_type handling:
    config_value    → sets key = expected_value
    config_contains → merges required_values into the list at key
    config_set      → skipped (no deterministic value; returns in skipped list)
    file_content    → skipped (repository governance, not a settings value)
    file_exists     → skipped (repository governance, not a settings value)
"""

from typing import Any

from clauditor.models.check import Check, CheckType, Scope

# Ordered highest → lowest precedence (mirrors aggregator.CONFIG_SCOPE_PRECEDENCE)
_SCOPE_PRECEDENCE: list[Scope] = [
    Scope.MANAGED,
    Scope.LOCAL,
    Scope.PROJECT,
    Scope.USER,
]

# Where each scope's settings file lives (for user-facing hints)
SCOPE_PATHS: dict[Scope, str] = {
    Scope.MANAGED: (
        "macOS:   /Library/Application Support/ClaudeCode/managed-settings.json\n"
        "Linux:   /etc/claude-code/managed-settings.json\n"
        "Windows: C:\\ProgramData\\ClaudeCode\\managed-settings.json"
    ),
    Scope.LOCAL: ".claude/settings.local.json  (gitignored, current repo)",
    Scope.PROJECT: ".claude/settings.json  (committed to git, shared with team)",
    Scope.USER: "~/.claude/settings.json  (personal, all projects)",
}

# Check types that produce settings values
_GENERATABLE_TYPES: frozenset[CheckType] = frozenset(
    [CheckType.CONFIG_VALUE, CheckType.CONFIG_CONTAINS]
)

# Check types skipped because they require manual input or are repo-level
_MANUAL_TYPES: frozenset[CheckType] = frozenset([CheckType.CONFIG_SET])
_REPO_TYPES: frozenset[CheckType] = frozenset([CheckType.FILE_CONTENT, CheckType.FILE_EXISTS])


def _applicable_scopes(target: Scope) -> frozenset[Scope]:
    """Return all scopes at or below target in the precedence chain."""
    idx = _SCOPE_PRECEDENCE.index(target)
    return frozenset(_SCOPE_PRECEDENCE[idx:])


def _set_nested(data: dict[str, Any], key: str, value: Any) -> None:
    """
    Write a dot-notation key into a nested dict.
    For list values, merges with any existing list (no duplicates).
    """
    parts = key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]

    final = parts[-1]
    if isinstance(value, list):
        existing = current.get(final)
        if isinstance(existing, list):
            for item in value:
                if item not in existing:
                    existing.append(item)
        else:
            current[final] = list(value)
    else:
        current[final] = value


def generate_settings(
    checks: list[Check],
    target_scope: Scope,
    severity_filter: list[str] | None = None,
    check_filter: list[str] | None = None,
) -> tuple[dict[str, Any], list[Check], list[Check]]:
    """
    Build a settings dict from the given checks.

    Args:
        checks:          All loaded checks.
        target_scope:    Scope level for the generated file.
        severity_filter: If set, only include checks at these severity levels.
        check_filter:    If set, only include these check IDs.

    Returns:
        (settings, skipped_manual, skipped_repo):
            settings        — dict ready to JSON-serialize
            skipped_manual  — config_set checks that need manual values
            skipped_repo    — repository-level checks (no settings value)
    """
    applicable = _applicable_scopes(target_scope)

    settings: dict[str, Any] = {}
    skipped_manual: list[Check] = []
    skipped_repo: list[Check] = []

    # Build id/severity sets for the filters applied above
    severity_upper = {s.upper() for s in severity_filter} if severity_filter else None
    check_ids = {cid.strip().upper() for cid in check_filter} if check_filter else None

    for check in checks:
        # Apply filters (same as above, but we iterate all checks for repo reporting)
        if severity_upper and check.severity.value not in severity_upper:
            continue
        if check_ids and check.id not in check_ids:
            continue

        # Repository checks: always skipped for settings generation, just reported
        if check.check_type in _REPO_TYPES or Scope.REPOSITORY in check.scope:
            skipped_repo.append(check)
            continue

        # Out of target scope: silently skip
        if not any(s in applicable for s in check.scope):
            continue

        # Requires manual input: can't generate a value
        if check.check_type in _MANUAL_TYPES:
            skipped_manual.append(check)
            continue

        cfg = check.check_config

        if check.check_type == CheckType.CONFIG_VALUE:
            _set_nested(settings, cfg["key"], cfg["expected_value"])

        elif check.check_type == CheckType.CONFIG_CONTAINS:
            _set_nested(settings, cfg["key"], cfg["required_values"])

    return settings, skipped_manual, skipped_repo
