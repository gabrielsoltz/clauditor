from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Scope(StrEnum):
    USER = "user"  # ~/.claude/settings.json (you, across all projects)
    PROJECT = "project"  # .claude/settings.json (all collaborators, committed to git)
    LOCAL = "local"  # .claude/settings.local.json (you, this repo only, gitignored)
    MANAGED = "managed"  # Server-managed settings deployed by IT (highest precedence)
    REPOSITORY = "repository"  # Repo-level files (CODEOWNERS, etc.) — Clauditor extension


class CheckType(StrEnum):
    CONFIG_VALUE = "config_value"  # Check a key/value in a JSON settings file
    CONFIG_CONTAINS = "config_contains"  # Check a key (list) contains all required values
    CONFIG_SET = "config_set"  # Check a key is present and non-empty (any truthy value)
    CONFIG_ABSENT = "config_absent"  # Check a key is NOT present (dangerous keys in project/local)
    CONFIG_NOT_CONTAINS = (
        "config_not_contains"  # Check a key (list) does NOT contain forbidden values
    )
    FILE_CONTENT = "file_content"  # Check content inside a file
    FILE_EXISTS = "file_exists"  # Check that a file exists


class Check(BaseModel):
    id: str = Field(..., pattern=r"^CC\d{3,}$", description="Unique check ID, e.g. CC001")
    name: str
    description: str
    scope: list[Scope] = Field(..., min_length=1)
    severity: Severity
    threat: str = Field(..., description="Threat mitigated by this check")
    category: str = Field(..., description="e.g. permissions, access_control, supply_chain")
    check_type: CheckType
    check_config: dict[str, Any] = Field(..., description="Check-type-specific configuration")
    remediation: str
    fix_available: bool = False
    references: list[str] = Field(default_factory=list)

    @field_validator("scope", mode="before")
    @classmethod
    def normalize_scope(_cls: Any, v: Any) -> Any:
        if isinstance(v, list):
            return [s.lower() if isinstance(s, str) else s for s in v]
        return v
