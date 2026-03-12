"""Tests for the YAML check loader."""

import pytest

from clauditor.loader import load_check, load_checks
from clauditor.models.check import CheckType, Scope, Severity
from tests.conftest import CHECKS_FIXTURES_DIR


class TestLoadBuiltinChecks:
    def test_loads_two_builtin_checks(self) -> None:
        checks = load_checks()
        assert len(checks) == 2

    def test_check_ids_are_unique(self) -> None:
        checks = load_checks()
        ids = [c.id for c in checks]
        assert len(ids) == len(set(ids))

    def test_cc001_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc001 = checks["CC001"]
        assert cc001.name == "CODEOWNERS Enforcement for Claude Code Paths"
        assert cc001.severity == Severity.HIGH
        assert cc001.check_type == CheckType.FILE_CONTENT
        assert Scope.REPOSITORY in cc001.scope
        assert cc001.fix_available is True
        assert len(cc001.references) > 0

    def test_cc002_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc002 = checks["CC002"]
        assert cc002.name == "Disable Bypass Permissions Mode"
        assert cc002.severity == Severity.CRITICAL
        assert cc002.check_type == CheckType.CONFIG_VALUE
        assert Scope.USER in cc002.scope
        assert Scope.PROJECT in cc002.scope
        assert Scope.LOCAL in cc002.scope
        assert Scope.MANAGED in cc002.scope
        assert cc002.check_config["key"] == "disableBypassPermissionsMode"
        assert cc002.check_config["expected_value"] == "disable"


class TestLoadCustomChecks:
    def test_loads_fixture_checks(self) -> None:
        checks = load_checks(CHECKS_FIXTURES_DIR)
        ids = [c.id for c in checks]
        assert "CC901" in ids
        assert "CC902" in ids
        assert "CC903" in ids

    def test_cc901_is_config_value_type(self) -> None:
        checks = {c.id: c for c in load_checks(CHECKS_FIXTURES_DIR)}
        assert checks["CC901"].check_type == CheckType.CONFIG_VALUE

    def test_cc902_is_file_content_type(self) -> None:
        checks = {c.id: c for c in load_checks(CHECKS_FIXTURES_DIR)}
        assert checks["CC902"].check_type == CheckType.FILE_CONTENT

    def test_cc903_is_file_exists_type(self) -> None:
        checks = {c.id: c for c in load_checks(CHECKS_FIXTURES_DIR)}
        assert checks["CC903"].check_type == CheckType.FILE_EXISTS


class TestLoadInvalidChecks:
    def test_invalid_id_skipped_with_warning(self) -> None:
        # invalid_bad_id.yaml and invalid_missing_scope.yaml should be skipped
        with pytest.warns(UserWarning):
            checks = load_checks(CHECKS_FIXTURES_DIR)
        # Valid checks still load
        assert any(c.id == "CC901" for c in checks)

    def test_load_check_invalid_id_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid check definition"):
            load_check(CHECKS_FIXTURES_DIR / "invalid_bad_id.yaml")

    def test_load_check_missing_field_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid check definition"):
            load_check(CHECKS_FIXTURES_DIR / "invalid_missing_scope.yaml")
