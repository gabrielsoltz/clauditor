"""Tests for the settings generator."""

from clauditor.generator import generate_settings
from clauditor.models.check import CheckType, Scope, Severity
from tests.conftest import make_check


def _cv(id: str, key: str, value: object, scope: list[Scope]) -> object:
    """Shorthand: config_value check."""
    return make_check(
        id=id,
        check_type=CheckType.CONFIG_VALUE,
        check_config={"key": key, "expected_value": value},
        scope=scope,
    )


def _cc(id: str, key: str, values: list[str], scope: list[Scope]) -> object:
    """Shorthand: config_contains check."""
    return make_check(
        id=id,
        check_type=CheckType.CONFIG_CONTAINS,
        check_config={"key": key, "required_values": values},
        scope=scope,
    )


def _cs(id: str, key: str, scope: list[Scope]) -> object:
    """Shorthand: config_set check."""
    return make_check(
        id=id,
        check_type=CheckType.CONFIG_SET,
        check_config={"key": key},
        scope=scope,
    )


def _fc(id: str, scope: list[Scope]) -> object:
    """Shorthand: file_content check."""
    return make_check(
        id=id,
        check_type=CheckType.FILE_CONTENT,
        check_config={"search_paths": ["CODEOWNERS"], "required_entries": []},
        scope=scope,
    )


class TestGenerateSettingsScope:
    def test_managed_scope_includes_all_config_checks(self) -> None:
        checks = [
            _cv("CC901", "keyA", True, [Scope.MANAGED]),
            _cv("CC902", "keyB", "val", [Scope.USER]),
            _cv("CC903", "keyC", False, [Scope.PROJECT]),
        ]
        settings, _, _ = generate_settings(checks, target_scope=Scope.MANAGED)
        assert "keyA" in settings
        assert "keyB" in settings
        assert "keyC" in settings

    def test_user_scope_includes_only_user_checks(self) -> None:
        checks = [
            _cv("CC901", "keyA", True, [Scope.MANAGED]),
            _cv("CC902", "keyB", "val", [Scope.USER]),
            _cv("CC903", "keyC", "val", [Scope.PROJECT, Scope.USER]),
        ]
        settings, _, _ = generate_settings(checks, target_scope=Scope.USER)
        assert "keyA" not in settings
        assert "keyB" in settings
        assert "keyC" in settings

    def test_project_scope_excludes_managed_only_checks(self) -> None:
        checks = [
            _cv("CC901", "managed_key", True, [Scope.MANAGED]),
            _cv("CC902", "project_key", True, [Scope.PROJECT, Scope.USER]),
        ]
        settings, _, _ = generate_settings(checks, target_scope=Scope.PROJECT)
        assert "managed_key" not in settings
        assert "project_key" in settings

    def test_local_scope_excludes_managed_only(self) -> None:
        checks = [
            _cv("CC901", "managed_key", True, [Scope.MANAGED]),
            _cv("CC902", "local_key", True, [Scope.LOCAL, Scope.PROJECT, Scope.USER]),
        ]
        settings, _, _ = generate_settings(checks, target_scope=Scope.LOCAL)
        assert "managed_key" not in settings
        assert "local_key" in settings


class TestGenerateSettingsValues:
    def test_config_value_bool_true(self) -> None:
        checks = [_cv("CC901", "sandbox.enabled", True, [Scope.USER])]
        settings, _, _ = generate_settings(checks, target_scope=Scope.USER)
        assert settings["sandbox"]["enabled"] is True

    def test_config_value_bool_false(self) -> None:
        checks = [_cv("CC901", "enableAllProjectMcpServers", False, [Scope.MANAGED])]
        settings, _, _ = generate_settings(checks, target_scope=Scope.MANAGED)
        assert settings["enableAllProjectMcpServers"] is False

    def test_config_value_string(self) -> None:
        checks = [_cv("CC901", "disableBypassPermissionsMode", "disable", [Scope.USER])]
        settings, _, _ = generate_settings(checks, target_scope=Scope.USER)
        assert settings["disableBypassPermissionsMode"] == "disable"

    def test_config_contains_creates_list(self) -> None:
        checks = [
            _cc("CC901", "permissions.deny", ["Read(.env)", "Read(secrets/**)"], [Scope.MANAGED])
        ]
        settings, _, _ = generate_settings(checks, target_scope=Scope.MANAGED)
        assert settings["permissions"]["deny"] == ["Read(.env)", "Read(secrets/**)"]

    def test_config_contains_merges_multiple_checks_same_key(self) -> None:
        """Two checks writing to permissions.deny should be merged."""
        checks = [
            _cc("CC901", "permissions.deny", ["Read(.env)"], [Scope.MANAGED]),
            _cc("CC902", "permissions.deny", ["Bash(curl:*)", "Bash(wget:*)"], [Scope.MANAGED]),
        ]
        settings, _, _ = generate_settings(checks, target_scope=Scope.MANAGED)
        deny = settings["permissions"]["deny"]
        assert "Read(.env)" in deny
        assert "Bash(curl:*)" in deny
        assert "Bash(wget:*)" in deny

    def test_config_contains_no_duplicates_on_merge(self) -> None:
        checks = [
            _cc("CC901", "permissions.deny", ["Read(.env)", "Read(secrets/**)"], [Scope.MANAGED]),
            _cc("CC902", "permissions.deny", ["Read(.env)", "Bash(curl:*)"], [Scope.MANAGED]),
        ]
        settings, _, _ = generate_settings(checks, target_scope=Scope.MANAGED)
        deny = settings["permissions"]["deny"]
        assert deny.count("Read(.env)") == 1

    def test_nested_dot_notation(self) -> None:
        checks = [_cv("CC901", "sandbox.filesystem.enabled", True, [Scope.USER])]
        settings, _, _ = generate_settings(checks, target_scope=Scope.USER)
        assert settings["sandbox"]["filesystem"]["enabled"] is True


class TestGenerateSettingsSkipped:
    def test_config_set_skipped_returned_in_manual(self) -> None:
        checks = [_cs("CC901", "forceLoginOrgUUID", [Scope.MANAGED])]
        settings, skipped_manual, _ = generate_settings(checks, target_scope=Scope.MANAGED)
        assert "forceLoginOrgUUID" not in settings
        assert len(skipped_manual) == 1
        assert skipped_manual[0].id == "CC901"

    def test_file_content_skipped_returned_in_repo(self) -> None:
        checks = [_fc("CC901", [Scope.REPOSITORY])]
        settings, _, skipped_repo = generate_settings(checks, target_scope=Scope.MANAGED)
        assert len(settings) == 0
        assert len(skipped_repo) == 1


class TestGenerateSettingsFilters:
    def test_severity_filter(self) -> None:
        checks = [
            make_check(
                id="CC901",
                check_type=CheckType.CONFIG_VALUE,
                check_config={"key": "keyA", "expected_value": True},
                severity=Severity.CRITICAL,
                scope=[Scope.USER],
            ),
            make_check(
                id="CC902",
                check_type=CheckType.CONFIG_VALUE,
                check_config={"key": "keyB", "expected_value": True},
                severity=Severity.LOW,
                scope=[Scope.USER],
            ),
        ]
        settings, _, _ = generate_settings(
            checks, target_scope=Scope.USER, severity_filter=["CRITICAL"]
        )
        assert "keyA" in settings
        assert "keyB" not in settings

    def test_check_id_filter(self) -> None:
        checks = [
            _cv("CC901", "keyA", True, [Scope.USER]),
            _cv("CC902", "keyB", True, [Scope.USER]),
        ]
        settings, _, _ = generate_settings(checks, target_scope=Scope.USER, check_filter=["CC901"])
        assert "keyA" in settings
        assert "keyB" not in settings

    def test_empty_result_when_no_checks_match(self) -> None:
        checks = [_cv("CC901", "keyA", True, [Scope.MANAGED])]
        settings, _, _ = generate_settings(checks, target_scope=Scope.USER)
        assert settings == {}
