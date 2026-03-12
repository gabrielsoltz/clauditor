"""Checker for config_not_contains check type.

Verifies that a specific key in the JSON settings file (expected to be a list)
does NOT contain any of the forbidden values.

Use this to detect dangerous allow-all rules (e.g. bare "Bash" in permissions.allow).
If the key is absent or the settings file is missing, the check passes — absence
of a list means the forbidden values cannot be present.

check_config schema:
  key:              str    # Dot-notation key, e.g. "permissions.allow"
  forbidden_values: list   # Values that must NOT be in the list
"""

from typing import Any

from clauditor.models.check import Check
from clauditor.models.finding import Finding, FindingStatus
from clauditor.providers.base import BaseProvider

from .base import BaseChecker
from .config_value import _get_nested


class ConfigNotContainsChecker(BaseChecker):
    def run(self, check: Check, provider: BaseProvider) -> Finding:
        cfg = check.check_config
        key: str = cfg["key"]
        forbidden: list[Any] = cfg["forbidden_values"]

        settings = provider.get_settings()
        root = provider.get_root()
        target = str(root / "settings.json") if root else str(provider.scope.value)

        if not settings:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.PASS,
                scope=provider.scope,
                target=target,
                message="Settings file not found or empty — no forbidden values present.",
                severity=check.severity,
                remediation=check.remediation,
                references=check.references,
            )

        actual, found = _get_nested(settings, key)

        if not found or actual is None:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.PASS,
                scope=provider.scope,
                target=target,
                message=f"Key '{key}' is not set — no forbidden values present.",
                severity=check.severity,
                remediation=check.remediation,
                references=check.references,
            )

        if not isinstance(actual, list):
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.FAIL,
                scope=provider.scope,
                target=target,
                message=f"Key '{key}' is {actual!r} (expected a list).",
                severity=check.severity,
                remediation=check.remediation,
                references=check.references,
            )

        found_forbidden = [v for v in forbidden if v in actual]
        if found_forbidden:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.FAIL,
                scope=provider.scope,
                target=target,
                message=f"Key '{key}' contains forbidden entries: {found_forbidden}.",
                severity=check.severity,
                remediation=check.remediation,
                references=check.references,
            )

        return Finding(
            check_id=check.id,
            check_name=check.name,
            status=FindingStatus.PASS,
            scope=provider.scope,
            target=target,
            message=f"Key '{key}' does not contain any forbidden entries.",
            severity=check.severity,
            remediation=check.remediation,
            references=check.references,
        )
