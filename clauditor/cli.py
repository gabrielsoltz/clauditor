"""Clauditor CLI entry point."""

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from clauditor import __version__
from clauditor.output.console import print_banner, print_findings, print_summary
from clauditor.scanner import run_scan

app = typer.Typer(
    name="clauditor",
    help="Security configuration scanner for Claude Code.",
    add_completion=False,
    rich_markup_mode="rich",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"clauditor {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-V", callback=_version_callback, is_eager=True, help="Show version and exit."),
    ] = None,
) -> None:
    pass


@app.command()
def scan(
    path: Annotated[
        Optional[Path],
        typer.Option("--path", "-p", help="Path to a local repository to scan.", show_default=False),
    ] = None,
    url: Annotated[
        Optional[str],
        typer.Option("--url", "-u", help="URL of a remote git repository to clone and scan.", show_default=False),
    ] = None,
    user_only: Annotated[
        bool,
        typer.Option("--user-only", help="Only scan user scope (~/.claude/settings.json)."),
    ] = False,
    no_user: Annotated[
        bool,
        typer.Option("--no-user", help="Skip user scope scan."),
    ] = False,
    checks_dir: Annotated[
        Optional[Path],
        typer.Option("--checks-dir", help="Directory with custom YAML check definitions.", show_default=False),
    ] = None,
    severity: Annotated[
        Optional[str],
        typer.Option("--severity", "-s", help="Comma-separated severity filter, e.g. CRITICAL,HIGH"),
    ] = None,
    scope: Annotated[
        Optional[str],
        typer.Option("--scope", help="Comma-separated scope filter, e.g. user,project,repository"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show remediation steps for failed checks."),
    ] = False,
    exit_code: Annotated[
        bool,
        typer.Option("--exit-code", help="Exit with code 1 if any FAIL findings are found."),
    ] = False,
) -> None:
    """
    Scan Claude Code security configurations.

    By default scans the current directory as a repository and includes user scope settings.

    Examples:

      clauditor                              # Scan current directory + user scope
      clauditor --path /path/to/repo        # Scan a specific local repo
      clauditor --url https://github.com/org/repo  # Clone and scan a remote repo
      clauditor --user-only                 # Only scan user scope settings
      clauditor --severity CRITICAL,HIGH    # Only run critical/high checks
      clauditor -v                          # Show remediation steps
    """
    print_banner()

    # Resolve run mode
    if user_only and url:
        typer.echo("Error: --user-only and --url are mutually exclusive.", err=True)
        raise typer.Exit(1)

    if user_only:
        repo_root = None
        include_user = True
        repo_url = None
    elif url:
        repo_root = None
        include_user = not no_user
        repo_url = url
    else:
        repo_root = path or Path.cwd()
        include_user = not no_user
        repo_url = None

    severity_filter = [s.strip() for s in severity.split(",")] if severity else None
    scope_filter = [s.strip() for s in scope.split(",")] if scope else None

    try:
        findings = run_scan(
            repo_root=repo_root,
            repo_url=repo_url,
            include_user=include_user,
            checks_dir=checks_dir,
            severity_filter=severity_filter,
            scope_filter=scope_filter,
        )
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    print_findings(findings, verbose=verbose)
    print_summary(findings)

    if exit_code:
        from clauditor.models.finding import FindingStatus
        has_failures = any(f.status == FindingStatus.FAIL for f in findings)
        if has_failures:
            raise typer.Exit(1)


@app.command()
def list_checks(
    checks_dir: Annotated[
        Optional[Path],
        typer.Option("--checks-dir", help="Custom checks directory.", show_default=False),
    ] = None,
) -> None:
    """List all available checks."""
    from clauditor.loader import load_checks
    from rich.console import Console
    from rich.table import Table
    from rich import box

    checks = load_checks(checks_dir)
    console = Console()

    table = Table(box=box.ROUNDED, title="Available Checks", title_style="bold")
    table.add_column("ID", style="bold", width=6)
    table.add_column("Name", min_width=30)
    table.add_column("Severity", width=10)
    table.add_column("Scope", min_width=20)
    table.add_column("Category", width=16)
    table.add_column("Check Type", width=14)

    for c in checks:
        table.add_row(
            c.id,
            c.name,
            c.severity.value,
            ", ".join(s.value for s in c.scope),
            c.category,
            c.check_type.value,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(checks)} check(s)[/dim]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
