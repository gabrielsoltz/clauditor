"""Tests for the config_contains checker."""

from clauditor.checkers.config_contains import ConfigContainsChecker
from clauditor.models.check import CheckType, Scope
from clauditor.models.finding import FindingStatus
from tests.conftest import StubProvider, make_check

CHECKER = ConfigContainsChecker()

DENY_CHECK = make_check(
    id="CC904",
    check_type=CheckType.CONFIG_CONTAINS,
    check_config={
        "key": "permissions.deny",
        "required_values": ["Read(.env)", "Read(secrets/**)"],
    },
)


def _provider(settings: dict) -> StubProvider:  # type: ignore[type-arg]
    return StubProvider(scope=Scope.MANAGED, settings=settings)


class TestConfigContainsPass:
    def test_all_required_values_present(self) -> None:
        provider = _provider({"permissions": {"deny": ["Read(.env)", "Read(secrets/**)"]}})
        finding = CHECKER.run(DENY_CHECK, provider)
        assert finding.status == FindingStatus.PASS

    def test_extra_values_still_pass(self) -> None:
        """List may contain more entries than required — still PASS."""
        provider = _provider(
            {"permissions": {"deny": ["Read(.env)", "Read(secrets/**)", "Write(**/.env)"]}}
        )
        finding = CHECKER.run(DENY_CHECK, provider)
        assert finding.status == FindingStatus.PASS


class TestConfigContainsFail:
    def test_key_missing(self) -> None:
        provider = _provider({"someOtherKey": "value"})
        finding = CHECKER.run(DENY_CHECK, provider)
        assert finding.status == FindingStatus.FAIL
        assert "permissions.deny" in finding.message

    def test_key_present_but_empty_list(self) -> None:
        provider = _provider({"permissions": {"deny": []}})
        finding = CHECKER.run(DENY_CHECK, provider)
        assert finding.status == FindingStatus.FAIL
        assert "missing" in finding.message

    def test_partial_entries_missing(self) -> None:
        provider = _provider({"permissions": {"deny": ["Read(.env)"]}})
        finding = CHECKER.run(DENY_CHECK, provider)
        assert finding.status == FindingStatus.FAIL
        assert "Read(secrets/**)" in finding.message

    def test_value_is_not_a_list(self) -> None:
        provider = _provider({"permissions": {"deny": "Read(.env)"}})
        finding = CHECKER.run(DENY_CHECK, provider)
        assert finding.status == FindingStatus.FAIL
        assert "expected a list" in finding.message


class TestConfigContainsSkip:
    def test_empty_settings(self) -> None:
        provider = StubProvider(scope=Scope.MANAGED, settings={})
        finding = CHECKER.run(DENY_CHECK, provider)
        assert finding.status == FindingStatus.SKIPPED


class TestConfigContainsMisc:
    def test_scope_reflected_in_finding(self) -> None:
        provider = _provider({"permissions": {"deny": ["Read(.env)", "Read(secrets/**)"]}})
        finding = CHECKER.run(DENY_CHECK, provider)
        assert finding.scope == Scope.MANAGED
