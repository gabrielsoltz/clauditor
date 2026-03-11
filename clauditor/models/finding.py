from enum import Enum

from pydantic import BaseModel, Field

from .check import Scope, Severity


class FindingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


class Finding(BaseModel):
    check_id: str
    check_name: str
    status: FindingStatus
    scope: Scope
    target: str = Field(..., description="File path or settings scope that was evaluated")
    message: str
    severity: Severity
    remediation: str = ""
    references: list[str] = []
