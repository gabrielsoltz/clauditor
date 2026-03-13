"""Checker for file_content check type.

Verifies that a file contains required entries (lines/patterns).

check_config schema:
  search_paths: list[str]       # Candidate file paths to look for (first found wins)
  required_entries: list[dict]  # Each entry has 'pattern' and optional 'owner'
    - pattern: str              # e.g. "/.claude/"
      owner: str                # e.g. "@security-team"
"""

from typing import Any

from clauditor.models.check import Check
from clauditor.models.finding import Finding, FindingStatus
from clauditor.providers.base import BaseProvider

from .base import BaseChecker


def _entry_present(content: str, pattern: str, owner: str | None) -> bool:
    """
    Check whether a file contains a line matching pattern + owner.
    Matching is whitespace-tolerant and case-insensitive for the owner.
    """
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        parts = stripped.split()
        if not parts:
            continue
        file_pattern = parts[0]
        owners = parts[1:] if len(parts) > 1 else []
        if file_pattern == pattern:
            if owner is None:
                return len(owners) > 0  # pattern must have at least one owner assigned
            if any(o.lower() == owner.lower() for o in owners):
                return True
    return False


class FileContentChecker(BaseChecker):
    def run(self, check: Check, provider: BaseProvider) -> Finding:
        cfg = check.check_config
        search_paths: list[str] = cfg.get("search_paths", [cfg.get("file", "")])
        required_entries: list[dict[str, Any]] = cfg.get("required_entries", [])

        # Find the first existing file among candidate paths
        found_path: str | None = None
        content: str | None = None
        for path in search_paths:
            content = provider.get_file(path)
            if content is not None:
                found_path = path
                break

        root = provider.get_root()
        target = (
            str(root / found_path)
            if (root and found_path)
            else (found_path or search_paths[0] if search_paths else "unknown")
        )

        if content is None:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.FAIL,
                scope=provider.scope,
                target=str(root / search_paths[0]) if root and search_paths else "unknown",
                message=f"No file found at any of: {', '.join(search_paths)}",
                severity=check.severity,
                remediation=check.remediation,
                references=check.references,
            )

        missing: list[str] = []
        for entry in required_entries:
            pattern = entry["pattern"]
            owner = entry.get("owner")
            if not _entry_present(content, pattern, owner):
                desc = f"{pattern} {owner}" if owner else pattern
                missing.append(desc)

        if missing:
            return Finding(
                check_id=check.id,
                check_name=check.name,
                status=FindingStatus.FAIL,
                scope=provider.scope,
                target=target,
                message=f"Missing required entries in {found_path}: {'; '.join(missing)}",
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
            message=f"All required entries found in {found_path}.",
            severity=check.severity,
            remediation=check.remediation,
            references=check.references,
        )
