"""Tests for the YAML check loader."""

import pytest

from clauditor.loader import load_check, load_checks
from clauditor.models.check import CheckType, Scope, Severity
from tests.conftest import CHECKS_FIXTURES_DIR


class TestLoadBuiltinChecks:
    def test_loads_builtin_checks(self) -> None:
        checks = load_checks()
        assert len(checks) == 33

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

    def test_cc003_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc003 = checks["CC003"]
        assert cc003.name == "Enforce Managed Permission Rules Only"
        assert cc003.severity == Severity.LOW
        assert cc003.check_type == CheckType.CONFIG_VALUE
        assert cc003.scope == [Scope.MANAGED]
        assert cc003.check_config["key"] == "allowManagedPermissionRulesOnly"
        assert cc003.check_config["expected_value"] is True

    def test_cc004_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc004 = checks["CC004"]
        assert cc004.name == "Deny Sensitive File Operations"
        assert cc004.severity == Severity.LOW
        assert cc004.check_type == CheckType.CONFIG_CONTAINS
        assert cc004.scope == [Scope.MANAGED]
        assert cc004.check_config["key"] == "permissions.deny"
        assert "Read(.env)" in cc004.check_config["required_values"]
        assert "Read(secrets/**)" in cc004.check_config["required_values"]

    def test_cc005_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc005 = checks["CC005"]
        assert cc005.name == "Disable Auto-Approval of Project MCP Servers"
        assert cc005.severity == Severity.LOW
        assert cc005.check_type == CheckType.CONFIG_VALUE
        assert cc005.scope == [Scope.MANAGED]
        assert cc005.check_config["key"] == "enableAllProjectMcpServers"
        assert cc005.check_config["expected_value"] is False

    def test_cc006_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc006 = checks["CC006"]
        assert cc006.name == "Enforce Managed Hooks Only"
        assert cc006.severity == Severity.LOW
        assert cc006.check_type == CheckType.CONFIG_VALUE
        assert cc006.scope == [Scope.MANAGED]
        assert cc006.check_config["key"] == "allowManagedHooksOnly"
        assert cc006.check_config["expected_value"] is True

    def test_cc007_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc007 = checks["CC007"]
        assert cc007.name == "Force SSO Login Method"
        assert cc007.severity == Severity.MEDIUM
        assert cc007.check_type == CheckType.CONFIG_VALUE
        assert cc007.scope == [Scope.MANAGED]
        assert cc007.check_config["key"] == "forceLoginMethod"
        assert cc007.check_config["expected_value"] == "claudeai"

    def test_cc008_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc008 = checks["CC008"]
        assert cc008.name == "Require SSO Organization UUID"
        assert cc008.severity == Severity.MEDIUM
        assert cc008.check_type == CheckType.CONFIG_SET
        assert cc008.scope == [Scope.MANAGED]
        assert cc008.check_config["key"] == "forceLoginOrgUUID"

    def test_cc009_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc009 = checks["CC009"]
        assert cc009.name == "Require Approval for Network-Fetching Tools"
        assert cc009.severity == Severity.LOW
        assert cc009.check_type == CheckType.CONFIG_CONTAINS
        assert cc009.scope == [Scope.MANAGED]
        assert "Bash(curl:*)" in cc009.check_config["required_values"]
        assert "Bash(wget:*)" in cc009.check_config["required_values"]

    def test_cc010_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc010 = checks["CC010"]
        assert cc010.name == "Enable Bash Sandboxing"
        assert cc010.severity == Severity.LOW
        assert cc010.check_type == CheckType.CONFIG_VALUE
        assert Scope.USER in cc010.scope
        assert Scope.PROJECT in cc010.scope
        assert Scope.LOCAL in cc010.scope
        assert Scope.MANAGED in cc010.scope
        assert cc010.check_config["key"] == "sandbox.enabled"
        assert cc010.check_config["expected_value"] is True

    def test_cc011_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc011 = checks["CC011"]
        assert cc011.name == "Restrict Sandbox Filesystem Write Paths"
        assert cc011.severity == Severity.MEDIUM
        assert cc011.check_type == CheckType.CONFIG_CONTAINS
        assert Scope.USER in cc011.scope
        assert Scope.MANAGED in cc011.scope
        assert cc011.check_config["key"] == "sandbox.filesystem.denyWrite"
        assert "/etc" in cc011.check_config["required_values"]
        assert "~/.ssh" in cc011.check_config["required_values"]

    def test_cc012_fields(self) -> None:
        checks = {c.id: c for c in load_checks()}
        cc012 = checks["CC012"]
        assert cc012.name == "Restrict Sandbox Filesystem Read Paths"
        assert cc012.severity == Severity.MEDIUM
        assert cc012.check_type == CheckType.CONFIG_CONTAINS
        assert Scope.USER in cc012.scope
        assert Scope.MANAGED in cc012.scope
        assert cc012.check_config["key"] == "sandbox.filesystem.denyRead"
        assert "~/.ssh" in cc012.check_config["required_values"]
        assert "~/.aws/credentials" in cc012.check_config["required_values"]


class TestLoadCustomChecks:
    def test_loads_fixture_checks(self) -> None:
        checks = load_checks(CHECKS_FIXTURES_DIR)
        ids = [c.id for c in checks]
        assert "CC901" in ids
        assert "CC902" in ids
        assert "CC903" in ids
        assert "CC904" in ids
        assert "CC905" in ids

    def test_cc901_is_config_value_type(self) -> None:
        checks = {c.id: c for c in load_checks(CHECKS_FIXTURES_DIR)}
        assert checks["CC901"].check_type == CheckType.CONFIG_VALUE

    def test_cc902_is_file_content_type(self) -> None:
        checks = {c.id: c for c in load_checks(CHECKS_FIXTURES_DIR)}
        assert checks["CC902"].check_type == CheckType.FILE_CONTENT

    def test_cc903_is_file_exists_type(self) -> None:
        checks = {c.id: c for c in load_checks(CHECKS_FIXTURES_DIR)}
        assert checks["CC903"].check_type == CheckType.FILE_EXISTS

    def test_cc904_is_config_contains_type(self) -> None:
        checks = {c.id: c for c in load_checks(CHECKS_FIXTURES_DIR)}
        assert checks["CC904"].check_type == CheckType.CONFIG_CONTAINS

    def test_cc905_is_config_set_type(self) -> None:
        checks = {c.id: c for c in load_checks(CHECKS_FIXTURES_DIR)}
        assert checks["CC905"].check_type == CheckType.CONFIG_SET


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
