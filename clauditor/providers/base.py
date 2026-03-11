"""Base provider interface for loading configuration data from different scopes."""

from abc import ABC, abstractmethod
from pathlib import Path

from clauditor.models.check import Scope


class BaseProvider(ABC):
    """A provider knows how to load configuration data for a specific scope."""

    scope: Scope

    @abstractmethod
    def get_settings(self) -> dict:
        """Return the parsed settings dict for this scope, or {} if not found."""
        ...

    @abstractmethod
    def get_file(self, relative_path: str) -> str | None:
        """Return file content at the given relative path, or None if not found."""
        ...

    @abstractmethod
    def get_root(self) -> Path | None:
        """Return the root directory this provider resolves paths against."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider has any data to offer."""
        ...
