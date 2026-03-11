"""Provider for repository-level file checks (CODEOWNERS, CLAUDE.md, etc.)."""

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from clauditor.models.check import Scope

from .base import BaseProvider


class RepositoryProvider(BaseProvider):
    """Reads files from a local repository root."""

    scope = Scope.REPOSITORY

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    def get_settings(self) -> dict[str, Any]:
        # Repository checks work on files, not settings dicts
        return {}

    def get_file(self, relative_path: str) -> str | None:
        target = self._repo_root / relative_path
        if target.exists() and target.is_file():
            try:
                return target.read_text()
            except OSError:
                return None
        return None

    def get_root(self) -> Path:
        return self._repo_root

    def is_available(self) -> bool:
        return self._repo_root.exists() and self._repo_root.is_dir()


def clone_repository(url: str) -> tuple[Path, tempfile.TemporaryDirectory[str]]:
    """
    Clone a remote repository to a temporary directory.
    Returns (repo_root, temp_dir). Caller must clean up temp_dir.
    """
    tmp = tempfile.TemporaryDirectory()
    try:
        result = subprocess.run(
            ["git", "clone", "--depth=1", url, tmp.name],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            tmp.cleanup()
            raise RuntimeError(f"git clone failed: {result.stderr.strip()}")
        return Path(tmp.name), tmp
    except Exception:
        tmp.cleanup()
        raise
