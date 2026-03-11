from clauditor.models.check import CheckType

from .base import BaseChecker
from .config_value import ConfigValueChecker
from .file_content import FileContentChecker
from .file_exists import FileExistsChecker

CHECKER_REGISTRY: dict[CheckType, BaseChecker] = {
    CheckType.CONFIG_VALUE: ConfigValueChecker(),
    CheckType.FILE_CONTENT: FileContentChecker(),
    CheckType.FILE_EXISTS: FileExistsChecker(),
}

__all__ = [
    "BaseChecker",
    "ConfigValueChecker",
    "FileContentChecker",
    "FileExistsChecker",
    "CHECKER_REGISTRY",
]
