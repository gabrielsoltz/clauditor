"""Load and validate check definitions from YAML files."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from clauditor.models.check import Check

# Built-in checks bundled with the package
BUILTIN_CHECKS_DIR = Path(__file__).parent.parent / "checks"


def load_check(path: Path) -> Check:
    """Parse and validate a single YAML check file."""
    raw = yaml.safe_load(path.read_text())
    try:
        return Check.model_validate(raw)
    except ValidationError as e:
        raise ValueError(f"Invalid check definition in {path}: {e}") from e


def load_checks(directory: Path | None = None) -> list[Check]:
    """
    Load all YAML check files from a directory.
    Defaults to the built-in checks/ directory.
    Skips files that fail validation (with a warning).
    """
    checks_dir = directory or BUILTIN_CHECKS_DIR
    checks: list[Check] = []
    errors: list[str] = []

    for yaml_file in sorted(checks_dir.glob("*.yaml")):
        try:
            checks.append(load_check(yaml_file))
        except (ValueError, yaml.YAMLError) as e:
            errors.append(str(e))

    if errors:
        import warnings
        for err in errors:
            warnings.warn(err, stacklevel=2)

    return checks
