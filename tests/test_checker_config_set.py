"""Tests for the config_set checker."""

from clauditor.checkers.config_set import ConfigSetChecker
from clauditor.models.check import CheckType, Scope
from clauditor.models.finding import FindingStatus
from tests.conftest import StubProvider, make_check

CHECKER = ConfigSetChecker()

UUID_CHECK = make_check(
    id="CC905",
    check_type=CheckType.CONFIG_SET,
    check_config={"key": "forceLoginOrgUUID"},
    scope=[Scope.MANAGED],
)

NESTED_CHECK = make_check(
    id="CC905",
    check_type=CheckType.CONFIG_SET,
    check_config={"key": "org.uuid"},
    scope=[Scope.MANAGED],
)


def _provider(settings: dict) -> StubProvider:  # type: ignore[type-arg]
    return StubProvider(scope=Scope.MANAGED, settings=settings)


class TestConfigSetPass:
    def test_key_with_string_value(self) -> None:
        provider = _provider({"forceLoginOrgUUID": "abc-123-def"})
        finding = CHECKER.run(UUID_CHECK, provider)
        assert finding.status == FindingStatus.PASS

    def test_nested_key_set(self) -> None:
        provider = _provider({"org": {"uuid": "abc-123"}})
        finding = CHECKER.run(NESTED_CHECK, provider)
        assert finding.status == FindingStatus.PASS


class TestConfigSetFail:
    def test_key_missing(self) -> None:
        provider = _provider({"otherKey": "value"})
        finding = CHECKER.run(UUID_CHECK, provider)
        assert finding.status == FindingStatus.FAIL
        assert "forceLoginOrgUUID" in finding.message

    def test_key_empty_string(self) -> None:
        provider = _provider({"forceLoginOrgUUID": ""})
        finding = CHECKER.run(UUID_CHECK, provider)
        assert finding.status == FindingStatus.FAIL

    def test_key_none_value(self) -> None:
        provider = _provider({"forceLoginOrgUUID": None})
        finding = CHECKER.run(UUID_CHECK, provider)
        assert finding.status == FindingStatus.FAIL

    def test_nested_key_missing(self) -> None:
        provider = _provider({"org": {}})
        finding = CHECKER.run(NESTED_CHECK, provider)
        assert finding.status == FindingStatus.FAIL


class TestConfigSetSkip:
    def test_empty_settings(self) -> None:
        provider = StubProvider(scope=Scope.MANAGED, settings={})
        finding = CHECKER.run(UUID_CHECK, provider)
        assert finding.status == FindingStatus.SKIPPED


class TestConfigSetMisc:
    def test_scope_reflected_in_finding(self) -> None:
        provider = _provider({"forceLoginOrgUUID": "abc-123"})
        finding = CHECKER.run(UUID_CHECK, provider)
        assert finding.scope == Scope.MANAGED
