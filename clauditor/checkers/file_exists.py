"""Checker for file_exists check type.

Verifies that one or more files are present in the repository.

check_config schema:
  paths: list[str]   # File paths to check for existence (all must exist unless any_of is true)
  any_of: bool       # If true, at least one path must exist (default: false = all must exist)
"""

from clauditor.models.check import Check
from clauditor.models.finding import Finding, FindingStatus
from clauditor.providers.base import BaseProvider

from .base import BaseChecker


class FileExistsChecker(BaseChecker):
    def run(self, check: Check, provider: BaseProvider) -> Finding:
        cfg = check.check_config
        paths: list[str] = cfg.get("paths", [])
        any_of: bool = cfg.get("any_of", False)

        root = provider.get_root()

        present = [p for p in paths if provider.get_file(p) is not None]
        missing = [p for p in paths if provider.get_file(p) is None]

        if any_of:
            status = FindingStatus.PASS if present else FindingStatus.FAIL
            message = (
                f"Found: {', '.join(present)}"
                if present
                else f"None of the expected files found: {', '.join(paths)}"
            )
        else:
            status = FindingStatus.PASS if not missing else FindingStatus.FAIL
            message = (
                f"All required files found: {', '.join(paths)}"
                if not missing
                else f"Missing required files: {', '.join(missing)}"
            )

        return Finding(
            check_id=check.id,
            check_name=check.name,
            status=status,
            scope=provider.scope,
            target=str(root) if root else "unknown",
            message=message,
            severity=check.severity,
            remediation=check.remediation,
            references=check.references,
        )
