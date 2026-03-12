"""Load and validate check definitions from YAML files."""

import warnings
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

import yaml
from pydantic import ValidationError

from clauditor.models.check import Check


def load_check(path: Path) -> Check:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    try:
        return Check.model_validate(raw)
    except ValidationError as e:
        raise ValueError(f"Invalid check definition in {path}: {e}") from e


def _load_check_from_resource(item: Traversable) -> Check:
    raw = yaml.safe_load(item.read_text(encoding="utf-8"))
    try:
        return Check.model_validate(raw)
    except ValidationError as e:
        raise ValueError(f"Invalid check definition in {item.name}: {e}") from e


def load_checks(directory: Path | None = None) -> list[Check]:
    checks: list[Check] = []
    errors: list[str] = []

    if directory is not None:
        for yaml_file in sorted(directory.glob("*.yaml")):
            try:
                checks.append(load_check(yaml_file))
            except (ValueError, yaml.YAMLError) as e:
                errors.append(str(e))
    else:
        checks_pkg = resources.files("clauditor.checks")
        for item in sorted(checks_pkg.iterdir(), key=lambda p: p.name):
            if item.name.endswith(".yaml"):
                try:
                    checks.append(_load_check_from_resource(item))
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
