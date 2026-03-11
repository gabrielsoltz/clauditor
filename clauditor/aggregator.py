"""
Aggregate raw per-(check, scope) findings into per-check results,
applying Claude Code's scope precedence rules.

Precedence (highest → lowest):
    managed > local > project > user

The 'repository' scope is independent and not part of the config precedence chain.

Rules:
- A scope is COVERED when a higher-priority scope already has status PASS,
  meaning that scope's value takes effect and the lower scope is irrelevant.
- Effective status of a check is determined by the highest-priority scope
  that is not SKIPPED. If all config scopes are SKIPPED the setting is not
  configured anywhere, which is treated as FAIL for security purposes.
"""

from dataclasses import dataclass, field

from clauditor.models.check import Scope, Severity
from clauditor.models.finding import Finding, FindingStatus

# Ordered from highest to lowest precedence (repository excluded — standalone)
CONFIG_SCOPE_PRECEDENCE: list[Scope] = [
    Scope.MANAGED,
    Scope.LOCAL,
    Scope.PROJECT,
    Scope.USER,
]


class DisplayStatus(str):
    """Extended status for display — adds COVERED and NA on top of FindingStatus values."""

    pass


COVERED = DisplayStatus("COVERED")
NA = DisplayStatus("NA")


@dataclass
class CheckResult:
    check_id: str
    check_name: str
    severity: Severity
    category: str
    # Raw finding per scope (only scopes the check applies to)
    scope_findings: dict[Scope, Finding] = field(default_factory=dict)
    # Display status per scope after precedence is applied
    scope_display: dict[Scope, DisplayStatus] = field(default_factory=dict)
    # Overall status after precedence
    effective_status: FindingStatus = FindingStatus.SKIPPED
    # First FAIL finding (used for remediation in verbose mode)
    fail_finding: Finding | None = None


def aggregate(findings: list[Finding]) -> list[CheckResult]:
    """
    Group findings by check_id, apply scope precedence, and return one
    CheckResult per check in the original check order.
    """
    # Group by check_id, preserving insertion order
    groups: dict[str, CheckResult] = {}
    for f in findings:
        if f.check_id not in groups:
            groups[f.check_id] = CheckResult(
                check_id=f.check_id,
                check_name=f.check_name,
                severity=f.severity,
                category=getattr(f, "category", ""),
            )
        groups[f.check_id].scope_findings[f.scope] = f

    for result in groups.values():
        _apply_precedence(result)

    return list(groups.values())


def _apply_precedence(result: CheckResult) -> None:
    """Mutate result in-place: fill scope_display and set effective_status."""
    findings = result.scope_findings

    # --- Handle repository scope independently ---
    if Scope.REPOSITORY in findings:
        f = findings[Scope.REPOSITORY]
        result.scope_display[Scope.REPOSITORY] = DisplayStatus(f.status.value)
        if f.status == FindingStatus.FAIL and result.fail_finding is None:
            result.fail_finding = f

    # --- Handle config scopes with precedence ---
    config_scopes_present = [s for s in CONFIG_SCOPE_PRECEDENCE if s in findings]

    if not config_scopes_present:
        # Check only applies to repository scope
        repo_finding = findings.get(Scope.REPOSITORY)
        if repo_finding:
            result.effective_status = repo_finding.status
        return

    # Find the effective (highest-priority non-SKIPPED) scope
    effective_finding: Finding | None = None
    for scope in config_scopes_present:
        f = findings[scope]
        if f.status != FindingStatus.SKIPPED:
            effective_finding = f
            break

    # If all scopes are SKIPPED, the setting is not configured anywhere → FAIL
    if effective_finding is None:
        for scope in config_scopes_present:
            result.scope_display[scope] = DisplayStatus(FindingStatus.SKIPPED.value)
        result.effective_status = FindingStatus.FAIL
        result.fail_finding = findings[config_scopes_present[0]]
        return

    effective_status = effective_finding.status

    # Walk scopes in precedence order: mark COVERED once we pass a PASS scope
    covered = False
    for scope in config_scopes_present:
        f = findings[scope]
        if covered:
            result.scope_display[scope] = COVERED
        else:
            result.scope_display[scope] = DisplayStatus(f.status.value)
            if f.status == FindingStatus.FAIL and result.fail_finding is None:
                result.fail_finding = f
            if f.status == FindingStatus.PASS:
                covered = True

    result.effective_status = effective_status

    # If effective is PASS and it came from a non-repository scope,
    # also ensure any repository result doesn't override the overall status
    if Scope.REPOSITORY in findings:
        repo = findings[Scope.REPOSITORY]
        if repo.status == FindingStatus.FAIL:
            result.effective_status = FindingStatus.FAIL
            if result.fail_finding is None:
                result.fail_finding = repo
