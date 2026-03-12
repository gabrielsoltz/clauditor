from clauditor.models.check import CheckType

from .base import BaseChecker
from .config_absent import ConfigAbsentChecker
from .config_contains import ConfigContainsChecker
from .config_not_contains import ConfigNotContainsChecker
from .config_set import ConfigSetChecker
from .config_value import ConfigValueChecker
from .file_content import FileContentChecker
from .file_exists import FileExistsChecker

CHECKER_REGISTRY: dict[CheckType, BaseChecker] = {
    CheckType.CONFIG_VALUE: ConfigValueChecker(),
    CheckType.CONFIG_CONTAINS: ConfigContainsChecker(),
    CheckType.CONFIG_SET: ConfigSetChecker(),
    CheckType.CONFIG_ABSENT: ConfigAbsentChecker(),
    CheckType.CONFIG_NOT_CONTAINS: ConfigNotContainsChecker(),
    CheckType.FILE_CONTENT: FileContentChecker(),
    CheckType.FILE_EXISTS: FileExistsChecker(),
}

__all__ = [
    "BaseChecker",
    "ConfigAbsentChecker",
    "ConfigContainsChecker",
    "ConfigNotContainsChecker",
    "ConfigSetChecker",
    "ConfigValueChecker",
    "FileContentChecker",
    "FileExistsChecker",
    "CHECKER_REGISTRY",
]
