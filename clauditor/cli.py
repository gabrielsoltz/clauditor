"""Clauditor CLI entry point."""

from pathlib import Path
from typing import Annotated

import typer

from clauditor import __version__
from clauditor.models.check import Scope
from clauditor.output.console import print_banner, print_findings, print_summary
from clauditor.scanner import run_scan

_VALID_BASE_LEVELS: list[Scope] = [Scope.USER, Scope.PROJECT, Scope.LOCAL, Scope.MANAGED]

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
def callback(
    _version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    pass


@app.command()
def scan(
    path: Annotated[
        Path | None,
        typer.Option(
            "--path", "-p", help="Path to a local repository to scan.", show_default=False
        ),
    ] = None,
    url: Annotated[
        str | None,
        typer.Option(
            "--url",
            "-u",
            help="URL of a remote git repository to clone and scan.",
            show_default=False,
        ),
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
        Path | None,
        typer.Option(
            "--checks-dir", help="Directory with custom YAML check definitions.", show_default=False
        ),
    ] = None,
    severity: Annotated[
        str | None,
        typer.Option(
            "--severity", "-s", help="Comma-separated severity filter, e.g. CRITICAL,HIGH"
        ),
    ] = None,
    scope: Annotated[
        str | None,
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
    base_level: Annotated[
        str,
        typer.Option(
            "--base-level",
            help=(
                "Minimum scope required for a check to PASS. "
                "Options: user, project, local, managed. "
                "Default: user (any passing scope counts). "
                "Use 'project' to require team-wide enforcement."
            ),
        ),
    ] = "user",
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
        base_level_scope = Scope(base_level.lower())
    except ValueError:
        valid = ", ".join(s.value for s in _VALID_BASE_LEVELS)
        typer.echo(f"Error: --base-level must be one of: {valid}", err=True)
        raise typer.Exit(1)
    if base_level_scope not in _VALID_BASE_LEVELS:
        valid = ", ".join(s.value for s in _VALID_BASE_LEVELS)
        typer.echo(f"Error: --base-level must be one of: {valid}", err=True)
        raise typer.Exit(1)

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

    print_findings(findings, verbose=verbose, base_level=base_level_scope)
    print_summary(findings, base_level=base_level_scope)

    if exit_code:
        from clauditor.models.finding import FindingStatus

        has_failures = any(f.status == FindingStatus.FAIL for f in findings)
        if has_failures:
            raise typer.Exit(1)


@app.command()
def list_checks(
    checks_dir: Annotated[
        Path | None,
        typer.Option("--checks-dir", help="Custom checks directory.", show_default=False),
    ] = None,
) -> None:
    """List all available checks."""
    from rich import box
    from rich.console import Console
    from rich.table import Table

    from clauditor.loader import load_checks

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


@app.command()
def generate(
    scope: Annotated[
        str,
        typer.Option(
            "--scope",
            "-s",
            help=(
                "Target scope for the generated settings file. "
                "Controls which checks are included: 'managed' includes all config checks; "
                "'user' includes only user-scoped checks. "
                "Options: user, project, local, managed."
            ),
        ),
    ] = "user",
    severity: Annotated[
        str | None,
        typer.Option("--severity", help="Comma-separated severity filter, e.g. CRITICAL,HIGH"),
    ] = None,
    checks: Annotated[
        str | None,
        typer.Option("--checks", help="Comma-separated check IDs to include, e.g. CC002,CC010"),
    ] = None,
    checks_dir: Annotated[
        Path | None,
        typer.Option(
            "--checks-dir", help="Directory with custom YAML check definitions.", show_default=False
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write JSON to this file instead of stdout."),
    ] = None,
) -> None:
    """
    Generate a Claude Code settings file that remediates selected checks.

    Produces a JSON settings file containing all configuration values needed
    to pass the checks applicable to the chosen scope level.

    Scope inclusion rules:
      managed  — all config checks (managed + local + project + user)
      local    — local, project, and user checks
      project  — project and user checks
      user     — user-scoped checks only

    Examples:

      clauditor generate                          # User settings file (default)
      clauditor generate --scope managed         # Full managed settings file
      clauditor generate --scope project         # Project-level settings
      clauditor generate --severity CRITICAL     # Only critical checks
      clauditor generate --checks CC002,CC010    # Specific checks only
      clauditor generate -o managed-settings.json
    """
    import json
    import sys

    from rich.console import Console
    from rich.syntax import Syntax

    from clauditor.generator import SCOPE_PATHS, generate_settings
    from clauditor.loader import load_checks

    err_console = Console(stderr=True)

    _VALID_GENERATE_SCOPES: list[Scope] = [Scope.USER, Scope.PROJECT, Scope.LOCAL, Scope.MANAGED]

    try:
        target_scope = Scope(scope.lower())
    except ValueError:
        valid = ", ".join(s.value for s in _VALID_GENERATE_SCOPES)
        typer.echo(f"Error: --scope must be one of: {valid}", err=True)
        raise typer.Exit(1)
    if target_scope not in _VALID_GENERATE_SCOPES:
        valid = ", ".join(s.value for s in _VALID_GENERATE_SCOPES)
        typer.echo(f"Error: --scope must be one of: {valid}", err=True)
        raise typer.Exit(1)

    severity_filter = [s.strip() for s in severity.split(",")] if severity else None
    check_filter = [c.strip() for c in checks.split(",")] if checks else None

    all_checks = load_checks(checks_dir)
    settings, skipped_manual, skipped_repo = generate_settings(
        all_checks,
        target_scope=target_scope,
        severity_filter=severity_filter,
        check_filter=check_filter,
    )

    json_str = json.dumps(settings, indent=2)

    if output:
        output.write_text(json_str)
        err_console.print(f"[green]✔[/green] Written to [bold]{output}[/bold]")
    else:
        if sys.stdout.isatty():
            Console().print(Syntax(json_str, "json", theme="monokai", line_numbers=False))
        else:
            print(json_str)

    # Summary to stderr so it never pollutes redirected JSON
    err_console.print()
    err_console.print(
        f"[bold]Scope:[/bold] [cyan]{target_scope.value}[/cyan]  "
        f"[dim](includes checks for: "
        f"{', '.join(s.value for s in _applicable_scopes_for_display(target_scope))})[/dim]"
    )
    err_console.print(f"[bold]Deploy to:[/bold]\n[dim]{SCOPE_PATHS[target_scope]}[/dim]")
    err_console.print(f"[bold]Settings generated:[/bold] {len(settings)} top-level key(s)")
    if skipped_manual:
        err_console.print()
        err_console.print(
            "[yellow]⚠ The following checks require manual configuration "
            "(no deterministic value can be generated):[/yellow]"
        )
        for c in skipped_manual:
            err_console.print(
                f"  [bold]{c.id}[/bold] {c.name}  [dim]key: {c.check_config['key']}[/dim]"
            )
    if skipped_repo:
        err_console.print()
        err_console.print(
            "[dim]Repository-level checks skipped (not a settings value): "
            + ", ".join(c.id for c in skipped_repo)
            + "[/dim]"
        )


def _applicable_scopes_for_display(target: Scope) -> list[Scope]:
    """Return scopes included for a given target, for display purposes."""
    from clauditor.generator import _SCOPE_PRECEDENCE

    idx = _SCOPE_PRECEDENCE.index(target)
    return _SCOPE_PRECEDENCE[idx:]


def main() -> None:
    app()


if __name__ == "__main__":
    main()
