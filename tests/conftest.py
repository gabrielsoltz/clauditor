"""Shared fixtures and helpers for Clauditor tests."""

from pathlib import Path
from typing import Any

import pytest

from clauditor.models.check import Check, CheckType, Scope, Severity
from clauditor.models.finding import Finding, FindingStatus
from clauditor.providers.base import BaseProvider

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CHECKS_FIXTURES_DIR = FIXTURES_DIR / "checks"
SETTINGS_FIXTURES_DIR = FIXTURES_DIR / "settings"
FILES_FIXTURES_DIR = FIXTURES_DIR / "files"


class StubProvider(BaseProvider):
    """In-memory provider for unit tests — no filesystem access."""

    def __init__(
        self,
        scope: Scope,
        settings: dict[str, Any] | None = None,
        files: dict[str, str] | None = None,
        root: Path | None = None,
    ) -> None:
        self.scope = scope
        self._settings = settings or {}
        self._files = files or {}
        self._root = root or Path("/stub/root")

    def get_settings(self) -> dict[str, Any]:
        return self._settings

    def get_file(self, relative_path: str) -> str | None:
        return self._files.get(relative_path)

    def get_root(self) -> Path:
        return self._root

    def is_available(self) -> bool:
        return bool(self._settings) or bool(self._files)


def make_check(
    id: str = "CC901",
    name: str = "Test Check",
    scope: list[Scope] | None = None,
    severity: Severity = Severity.HIGH,
    check_type: CheckType = CheckType.CONFIG_VALUE,
    check_config: dict[str, Any] | None = None,
) -> Check:
    return Check(
        id=id,
        name=name,
        description="Test description",
        scope=scope or [Scope.PROJECT],
        severity=severity,
        threat="Test threat",
        category="test",
        check_type=check_type,
        check_config=check_config or {},
        remediation="Test remediation",
    )


def make_finding(
    check_id: str = "CC901",
    status: FindingStatus = FindingStatus.PASS,
    scope: Scope = Scope.PROJECT,
    severity: Severity = Severity.HIGH,
) -> Finding:
    return Finding(
        check_id=check_id,
        check_name="Test Check",
        status=status,
        scope=scope,
        target="/stub/root/settings.json",
        message="Test message",
        severity=severity,
        remediation="Test remediation",
    )


@pytest.fixture
def stub_project_provider() -> StubProvider:
    return StubProvider(scope=Scope.PROJECT)


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR
