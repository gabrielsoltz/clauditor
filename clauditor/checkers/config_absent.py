"""Checker for config_absent check type.

Verifies that a specific key is NOT present in the JSON settings file.
Use this for settings that are dangerous when present in shared scopes
(e.g. apiKeyHelper in project settings executes arbitrary shell commands).

check_config schema:
  key: str    # Dot-notation key, e.g. "apiKeyHelper"
"""

from clauditor.models.check import Check
from clauditor.models.finding import Finding, FindingStatus
from clauditor.providers.base import BaseProvider

from .base import BaseChecker
from .config_value import _get_nested


class ConfigAbsentChecker(BaseChecker):
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
                status=FindingStatus.PASS,
                scope=provider.scope,
                target=target,
                message="Settings file not found or empty — key is absent.",
                severity=check.severity,
                remediation=check.remediation,
                references=check.references,
            )

        actual, found = _get_nested(settings, key)

        if found:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.FAIL,
                scope=provider.scope,
                target=target,
                message=f"Key '{key}' is present ({actual!r}) — must not exist in this scope.",
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
            message=f"Key '{key}' is absent as expected.",
            severity=check.severity,
            remediation=check.remediation,
            references=check.references,
        )
