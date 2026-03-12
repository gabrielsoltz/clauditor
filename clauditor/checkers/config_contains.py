"""Checker for config_contains check type.

Verifies that a specific key in the JSON settings file is a list that
contains all of the required values.

check_config schema:
  key:             str    # Dot-notation key, e.g. "permissions.deny"
  required_values: list   # All values that must be present in the list
"""

from typing import Any

from clauditor.models.check import Check
from clauditor.models.finding import Finding, FindingStatus
from clauditor.providers.base import BaseProvider

from .base import BaseChecker
from .config_value import _get_nested


class ConfigContainsChecker(BaseChecker):
    def run(self, check: Check, provider: BaseProvider) -> Finding:
        cfg = check.check_config
        key: str = cfg["key"]
        required: list[Any] = cfg["required_values"]

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

        if not found or actual is None:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.FAIL,
                scope=provider.scope,
                target=target,
                message=f"Key '{key}' is not set.",
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

        missing = [v for v in required if v not in actual]
        if missing:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.FAIL,
                scope=provider.scope,
                target=target,
                message=f"Key '{key}' is missing required entries: {missing}.",
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
            message=f"Key '{key}' contains all required entries.",
            severity=check.severity,
            remediation=check.remediation,
            references=check.references,
        )
