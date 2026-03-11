"""Core scanner: orchestrates checks against providers."""

from pathlib import Path

from clauditor.checkers import CHECKER_REGISTRY
from clauditor.loader import load_checks
from clauditor.models.check import Check, Scope
from clauditor.models.finding import Finding
from clauditor.providers import (
    BaseProvider,
    UserProvider,
    LocalProvider,
    ManagedProvider,
    ProjectProvider,
    RepositoryProvider,
    clone_repository,
)


def _build_providers(
    repo_root: Path | None,
    include_user: bool,
) -> dict[Scope, BaseProvider]:
    """
    Build the set of providers to use for this scan run.

    - Always includes UserProvider when include_user is True.
    - Includes project/local/repository providers when a repo_root is given.
    - Always tries ManagedProvider (platform-specific path).
    """
    providers: dict[Scope, BaseProvider] = {}

    if include_user:
        providers[Scope.USER] = UserProvider()

    managed = ManagedProvider()
    providers[Scope.MANAGED] = managed

    if repo_root is not None:
        providers[Scope.PROJECT] = ProjectProvider(repo_root)
        providers[Scope.LOCAL] = LocalProvider(repo_root)
        providers[Scope.REPOSITORY] = RepositoryProvider(repo_root)

    return providers


def run_scan(
    repo_root: Path | None = None,
    repo_url: str | None = None,
    include_user: bool = True,
    checks_dir: Path | None = None,
    severity_filter: list[str] | None = None,
    scope_filter: list[str] | None = None,
) -> list[Finding]:
    """
    Execute all checks and return a flat list of findings.

    Args:
        repo_root:      Path to a local repository to scan.
        repo_url:       URL of a remote repository to clone and scan.
        include_user:   Whether to include user scope (~/.claude/settings.json) checks.
        checks_dir:     Custom directory of YAML checks (defaults to built-in).
        severity_filter: Only run checks at these severity levels.
        scope_filter:   Only run checks targeting these scopes.

    Returns:
        List of Finding objects, one per (check, scope) pair evaluated.
    """
    tmp_dir = None

    try:
        # Resolve repository root
        if repo_url:
            repo_root, tmp_dir = clone_repository(repo_url)
        elif repo_root is None:
            repo_root = Path.cwd()

        providers = _build_providers(repo_root, include_user)
        checks = load_checks(checks_dir)

        # Apply filters
        if severity_filter:
            upper = [s.upper() for s in severity_filter]
            checks = [c for c in checks if c.severity.value in upper]
        if scope_filter:
            lower = [s.lower() for s in scope_filter]
            checks = [c for c in checks if any(sc.value in lower for sc in c.scope)]

        findings: list[Finding] = []

        for check in checks:
            checker = CHECKER_REGISTRY.get(check.check_type)
            if checker is None:
                continue  # Unknown check type — skip

            for scope in check.scope:
                provider = providers.get(scope)
                if provider is None:
                    # Scope not available in this run (e.g. no repo for project scope)
                    continue

                try:
                    finding = checker.run(check, provider)
                    findings.append(finding)
                except Exception as exc:
                    from clauditor.models.finding import FindingStatus
                    findings.append(
                        Finding(
                            check_id=check.id,
                            check_name=check.name,
                            status=FindingStatus.ERROR,
                            scope=scope,
                            target="unknown",
                            message=f"Checker raised an exception: {exc}",
                            severity=check.severity,
                            remediation=check.remediation,
                            references=check.references,
                        )
                    )

        return findings

    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()
