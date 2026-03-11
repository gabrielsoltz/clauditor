"""Providers that read Claude Code JSON settings files."""

import json
from pathlib import Path
from typing import Any, cast

from clauditor.models.check import Scope

from .base import BaseProvider


class UserProvider(BaseProvider):
    """Reads ~/.claude/settings.json (user scope: you, across all projects)."""

    scope = Scope.USER

    def __init__(self) -> None:
        self._path = Path.home() / ".claude" / "settings.json"

    def get_settings(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return cast(dict[str, Any], json.loads(self._path.read_text()))
        except (json.JSONDecodeError, OSError):
            return {}

    def get_file(self, relative_path: str) -> str | None:
        target = Path.home() / ".claude" / relative_path
        if target.exists():
            return target.read_text()
        return None

    def get_root(self) -> Path:
        return Path.home() / ".claude"

    def is_available(self) -> bool:
        return self._path.exists()


class ProjectProvider(BaseProvider):
    """Reads .claude/settings.json (project-level shared settings)."""

    scope = Scope.PROJECT

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root
        self._path = repo_root / ".claude" / "settings.json"

    def get_settings(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return cast(dict[str, Any], json.loads(self._path.read_text()))
        except (json.JSONDecodeError, OSError):
            return {}

    def get_file(self, relative_path: str) -> str | None:
        target = self._repo_root / ".claude" / relative_path
        if target.exists():
            return target.read_text()
        return None

    def get_root(self) -> Path:
        return self._repo_root / ".claude"

    def is_available(self) -> bool:
        return self._path.exists()


class LocalProvider(BaseProvider):
    """Reads .claude/settings.local.json (project-level local/gitignored settings)."""

    scope = Scope.LOCAL

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root
        self._path = repo_root / ".claude" / "settings.local.json"

    def get_settings(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return cast(dict[str, Any], json.loads(self._path.read_text()))
        except (json.JSONDecodeError, OSError):
            return {}

    def get_file(self, relative_path: str) -> str | None:
        target = self._repo_root / ".claude" / relative_path
        if target.exists():
            return target.read_text()
        return None

    def get_root(self) -> Path:
        return self._repo_root / ".claude"

    def is_available(self) -> bool:
        return self._path.exists()


class ManagedProvider(BaseProvider):
    """Reads managed settings (enterprise-deployed, platform-specific)."""

    scope = Scope.MANAGED

    MANAGED_PATHS = [
        # macOS
        Path("/Library/Application Support/ClaudeCode/managed-settings.json"),
        # Linux
        Path("/etc/claude-code/managed-settings.json"),
        # Windows (WSL path)
        Path("/mnt/c/ProgramData/ClaudeCode/managed-settings.json"),
    ]

    def __init__(self) -> None:
        self._path: Path | None = next((p for p in self.MANAGED_PATHS if p.exists()), None)

    def get_settings(self) -> dict[str, Any]:
        if self._path is None:
            return {}
        try:
            return cast(dict[str, Any], json.loads(self._path.read_text()))
        except (json.JSONDecodeError, OSError):
            return {}

    def get_file(self, relative_path: str) -> str | None:
        return None

    def get_root(self) -> Path | None:
        return self._path.parent if self._path else None

    def is_available(self) -> bool:
        return self._path is not None
