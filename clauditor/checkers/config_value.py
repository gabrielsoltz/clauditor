"""Checker for config_value check type.

Verifies that a specific key exists in the JSON settings file
and matches the expected value.

check_config schema:
  key: str                  # Dot-notation key, e.g. "disableBypassPermissionsMode"
  expected_value: any       # Expected value (string, bool, int, etc.)
"""

from clauditor.models.check import Check
from clauditor.models.finding import Finding, FindingStatus
from clauditor.providers.base import BaseProvider

from .base import BaseChecker


def _get_nested(data: dict, key: str):  # type: ignore[return]
    """Resolve a dot-notation key like 'permissions.allow' from a nested dict."""
    parts = key.split(".")
    current = data
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None, False
        current = current[part]
    return current, True


class ConfigValueChecker(BaseChecker):
    def run(self, check: Check, provider: BaseProvider) -> Finding:
        cfg = check.check_config
        key: str = cfg["key"]
        expected = cfg["expected_value"]

        settings = provider.get_settings()
        root = provider.get_root()
        target = str(root / "settings.json") if root else str(provider.scope.value)

        if not settings:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.SKIPPED,
                scope=provider.scope,
                target=target,
                message="Settings file not found or empty — check not applicable.",
                severity=check.severity,
                remediation=check.remediation,
                references=check.references,
            )

        actual, found = _get_nested(settings, key)

        if not found:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.FAIL,
                scope=provider.scope,
                target=target,
                message=f"Key '{key}' is not set (expected: {expected!r}).",
                severity=check.severity,
                remediation=check.remediation,
                references=check.references,
            )

        if actual == expected:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.PASS,
                scope=provider.scope,
                target=target,
                message=f"Key '{key}' is correctly set to {actual!r}.",
                severity=check.severity,
                remediation=check.remediation,
                references=check.references,
            )

        return Finding(
            check_id=check.id,
            check_name=check.name,
            status=FindingStatus.FAIL,
            scope=provider.scope,
            target=target,
            message=f"Key '{key}' is {actual!r} but expected {expected!r}.",
            severity=check.severity,
            remediation=check.remediation,
            references=check.references,
        )
