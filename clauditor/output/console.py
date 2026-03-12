"""Rich console output for scan results."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from clauditor.aggregator import COVERED, NA, aggregate
from clauditor.models.check import Scope, Severity
from clauditor.models.finding import Finding, FindingStatus

_SCOPE_INITIALS = {
    Scope.MANAGED: "M",
    Scope.LOCAL: "L",
    Scope.PROJECT: "P",
    Scope.USER: "U",
    Scope.REPOSITORY: "R",
}

console = Console()

_SEVERITY_COLORS = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan",
    Severity.INFO: "dim",
}

# Display order for scope columns (precedence order + repository last)
_SCOPE_COLUMN_ORDER = [
    Scope.MANAGED,
    Scope.LOCAL,
    Scope.PROJECT,
    Scope.USER,
    Scope.REPOSITORY,
]

_SCOPE_LABELS = {
    Scope.MANAGED: "managed",
    Scope.LOCAL: "local",
    Scope.PROJECT: "project",
    Scope.USER: "user",
    Scope.REPOSITORY: "repository",
}


def _effective_cell(status: FindingStatus) -> str:
    if status == FindingStatus.PASS:
        return "[bold green]✔ PASS[/]"
    if status == FindingStatus.FAIL:
        return "[bold red]✘ FAIL[/]"
    if status == FindingStatus.ERROR:
        return "[bold yellow]⚠ ERROR[/]"
    return "[dim]– SKIP[/]"


def _scope_icon(display_status: str) -> str:
    """Compact single-icon representation for per-scope columns."""
    if display_status == FindingStatus.PASS.value:
        return "[bold green]✔[/]"
    if display_status == FindingStatus.FAIL.value:
        return "[bold red]✘[/]"
    if display_status == FindingStatus.ERROR.value:
        return "[bold yellow]⚠[/]"
    if display_status == FindingStatus.SKIPPED.value:
        return "[dim]–[/]"
    if display_status == COVERED:
        return "[dim green]↑[/]"
    return "[dim]·[/]"  # NA


def print_banner() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Clauditor[/bold cyan] — Claude Code Security Scanner\n"
            "[dim]Auditing your Claude Code configuration for security issues[/dim]",
            border_style="cyan",
        )
    )
    console.print()


def print_findings(
    findings: list[Finding], verbose: bool = False, base_level: Scope = Scope.USER
) -> None:
    if not findings:
        console.print("[green]No findings to display.[/green]")
        return

    results = aggregate(findings, base_level=base_level)

    # Determine which scope columns are actually used across all checks
    active_scopes = [s for s in _SCOPE_COLUMN_ORDER if any(s in r.scope_findings for r in results)]

    table = Table(
        box=box.ROUNDED,
        show_lines=True,
        title="Scan Results",
        title_style="bold",
        expand=True,
    )
    table.add_column("ID", style="bold", no_wrap=True, width=5)
    table.add_column("Check", min_width=20, ratio=2)
    table.add_column("Severity", no_wrap=True, width=9)
    table.add_column("Status", no_wrap=True, width=10)
    for scope in active_scopes:
        table.add_column(_SCOPE_INITIALS[scope], no_wrap=True, width=3, justify="center")

    for r in results:
        sev_color = _SEVERITY_COLORS.get(r.severity, "white")
        sev_text = Text(r.severity.value, style=sev_color)

        scope_cells = []
        for scope in active_scopes:
            if scope not in r.scope_findings:
                scope_cells.append(_scope_icon(NA))
            else:
                scope_cells.append(_scope_icon(r.scope_display.get(scope, NA)))

        table.add_row(
            r.check_id,
            r.check_name,
            sev_text,
            _effective_cell(r.effective_status),
            *scope_cells,
        )

    console.print(table)

    if active_scopes:
        scope_names = "  ".join(
            f"[dim]{_SCOPE_INITIALS[s]}[/dim]=[dim]{_SCOPE_LABELS[s]}[/dim]" for s in active_scopes
        )
        console.print(
            f"[dim]Scopes: {scope_names}[/dim]  "
            "[bold green]✔[/bold green][dim]=pass[/dim]  "
            "[bold red]✘[/bold red][dim]=fail[/dim]  "
            "[dim green]↑[/dim green][dim]=covered by higher scope[/dim]  "
            "[dim]–=skip  ·=n/a[/dim]"
        )

    if verbose:
        shown: set[str] = set()
        for r in results:
            f = r.fail_finding
            if f and r.check_id not in shown and f.remediation:
                shown.add(r.check_id)
                console.print()
                console.rule(f"[bold]{r.check_id} Remediation[/bold]")
                console.print(f.remediation.strip())
                if f.references:
                    console.print("\n[bold]References:[/bold]")
                    for ref in f.references:
                        console.print(f"  • {ref}")


def print_summary(findings: list[Finding], base_level: Scope = Scope.USER) -> None:
    console.print()

    results = aggregate(findings, base_level=base_level)
    total = len(results)

    by_status: dict[str, int] = {}
    by_severity: dict[str, int] = {}

    for r in results:
        status_key = r.effective_status.value
        by_status[status_key] = by_status.get(status_key, 0) + 1
        if r.effective_status == FindingStatus.FAIL:
            by_severity[r.severity.value] = by_severity.get(r.severity.value, 0) + 1

    fails = by_status.get(FindingStatus.FAIL.value, 0)
    passes = by_status.get(FindingStatus.PASS.value, 0)
    errors = by_status.get(FindingStatus.ERROR.value, 0)
    skipped = by_status.get(FindingStatus.SKIPPED.value, 0)

    status_color = "green" if fails == 0 else "red"
    console.print(
        Panel(
            f"[bold]Checks:[/bold] {total}  "
            f"[bold green]Pass:[/bold green] {passes}  "
            f"[bold red]Fail:[/bold red] {fails}  "
            f"[bold yellow]Error:[/bold yellow] {errors}  "
            f"[dim]Skipped:[/dim] {skipped}",
            title=f"[{status_color}]Summary[/{status_color}]",
            border_style=status_color,
        )
    )

    if by_severity:
        parts = []
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            count = by_severity.get(sev, 0)
            if count:
                color = _SEVERITY_COLORS.get(Severity(sev), "white")
                parts.append(f"[{color}]{sev}: {count}[/{color}]")
        console.print("Failures by severity: " + "  ".join(parts))
