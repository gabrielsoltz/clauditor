"""Checker for config_set check type.

Verifies that a specific key exists in the JSON settings file and is set
to a non-empty, truthy value. Use this when the exact value cannot be
predetermined (e.g. an organization UUID) but its presence is required.

check_config schema:
  key: str    # Dot-notation key, e.g. "forceLoginOrgUUID"
"""

from clauditor.models.check import Check
from clauditor.models.finding import Finding, FindingStatus
from clauditor.providers.base import BaseProvider

from .base import BaseChecker
from .config_value import _get_nested


class ConfigSetChecker(BaseChecker):
    def run(self, check: Check, provider: BaseProvider) -> Finding:
        cfg = check.check_config
        key: str = cfg["key"]

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

        if not found or not actual:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.FAIL,
                scope=provider.scope,
                target=target,
                message=f"Key '{key}' is not set or is empty.",
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
            message=f"Key '{key}' is set.",
            severity=check.severity,
            remediation=check.remediation,
            references=check.references,
        )
