"""Tests for the config_value checker."""

import json

import pytest

from clauditor.checkers.config_value import ConfigValueChecker
from clauditor.models.check import Scope
from clauditor.models.finding import FindingStatus
from tests.conftest import (
    SETTINGS_FIXTURES_DIR,
    StubProvider,
    make_check,
)


@pytest.fixture
def checker() -> ConfigValueChecker:
    return ConfigValueChecker()


def _settings(filename: str) -> dict:
    return json.loads((SETTINGS_FIXTURES_DIR / filename).read_text())


class TestConfigValueCheckerPass:
    def test_correct_value(self, checker: ConfigValueChecker) -> None:
        check = make_check(
            check_config={"key": "disableBypassPermissionsMode", "expected_value": "disable"}
        )
        provider = StubProvider(
            scope=Scope.PROJECT,
            settings=_settings("bypass_disabled.json"),
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS
        assert "disableBypassPermissionsMode" in finding.message

    def test_nested_key(self, checker: ConfigValueChecker) -> None:
        check = make_check(
            check_config={"key": "permissions.allow", "expected_value": ["Bash", "Read"]}
        )
        provider = StubProvider(
            scope=Scope.PROJECT,
            settings=_settings("nested_key.json"),
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS

    def test_boolean_value(self, checker: ConfigValueChecker) -> None:
        check = make_check(
            check_config={"key": "enableAllProjectMcpServers", "expected_value": False}
        )
        provider = StubProvider(
            scope=Scope.PROJECT,
            settings={"enableAllProjectMcpServers": False},
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS


class TestConfigValueCheckerFail:
    def test_wrong_value(self, checker: ConfigValueChecker) -> None:
        check = make_check(
            check_config={"key": "disableBypassPermissionsMode", "expected_value": "disable"}
        )
        provider = StubProvider(
            scope=Scope.PROJECT,
            settings=_settings("bypass_wrong_value.json"),
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.FAIL
        assert "allow" in finding.message
        assert "disable" in finding.message

    def test_key_not_set(self, checker: ConfigValueChecker) -> None:
        check = make_check(
            check_config={"key": "disableBypassPermissionsMode", "expected_value": "disable"}
        )
        provider = StubProvider(scope=Scope.PROJECT, settings={"otherKey": "value"})
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.FAIL
        assert "not set" in finding.message

    def test_nested_key_missing(self, checker: ConfigValueChecker) -> None:
        check = make_check(check_config={"key": "permissions.deny", "expected_value": ["Bash"]})
        provider = StubProvider(
            scope=Scope.PROJECT,
            settings=_settings("nested_key.json"),
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.FAIL


class TestConfigValueCheckerSkip:
    def test_empty_settings(self, checker: ConfigValueChecker) -> None:
        check = make_check(
            check_config={"key": "disableBypassPermissionsMode", "expected_value": "disable"}
        )
        provider = StubProvider(scope=Scope.PROJECT, settings={})
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.SKIPPED

    def test_scope_reflected_in_finding(self, checker: ConfigValueChecker) -> None:
        check = make_check(
            scope=[Scope.USER],
            check_config={"key": "disableBypassPermissionsMode", "expected_value": "disable"},
        )
        provider = StubProvider(
            scope=Scope.USER,
            settings=_settings("bypass_disabled.json"),
        )
        finding = checker.run(check, provider)
        assert finding.scope == Scope.USER
