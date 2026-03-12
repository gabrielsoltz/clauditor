"""Load and validate check definitions from YAML files."""

import tempfile
import warnings
from importlib import resources
from pathlib import Path

import yaml
from pydantic import ValidationError

from clauditor.models.check import Check


def load_check(path: Path) -> Check:
    raw = yaml.safe_load(path.read_text())
    try:
        return Check.model_validate(raw)
    except ValidationError as e:
        raise ValueError(f"Invalid check definition in {path}: {e}") from e


def _materialize_builtin_checks() -> Path:
    """
    Return a real filesystem directory containing packaged YAML checks.
    This works both from source and from installed wheels.
    """
    checks_pkg = resources.files("clauditor.checks")

    tmpdir = tempfile.TemporaryDirectory()
    outdir = Path(tmpdir.name)

    # keep tempdir alive by attaching it to the path object
    outdir._tmpdir = tmpdir  # type: ignore[attr-defined]

    for item in checks_pkg.iterdir():
        if item.name.endswith(".yaml"):
            (outdir / item.name).write_text(item.read_text(), encoding="utf-8")

    return outdir


def load_checks(directory: Path | None = None) -> list[Check]:
    checks_dir = directory or _materialize_builtin_checks()

    checks: list[Check] = []
    errors: list[str] = []

    for yaml_file in sorted(checks_dir.glob("*.yaml")):
        try:
            checks.append(load_check(yaml_file))
        except (ValueError, yaml.YAMLError) as e:
            errors.append(str(e))

    for err in errors:
        warnings.warn(err, stacklevel=2)

    if directory is None and not checks:
        raise RuntimeError(
            "No built-in checks were found. This usually means the package data "
            "was not installed correctly."
        )

    return checks
