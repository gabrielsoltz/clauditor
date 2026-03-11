"""Base checker interface."""

from abc import ABC, abstractmethod

from clauditor.models.check import Check
from clauditor.models.finding import Finding
from clauditor.providers.base import BaseProvider


class BaseChecker(ABC):
    """A checker implements the logic for one check_type."""

    @abstractmethod
    def run(self, check: Check, provider: BaseProvider) -> Finding:
        """Execute the check against the provider and return a Finding."""
        ...
