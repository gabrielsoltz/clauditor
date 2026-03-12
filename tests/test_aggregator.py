"""Tests for the scope precedence aggregation logic."""

from clauditor.aggregator import COVERED, aggregate
from clauditor.models.check import Scope, Severity
from clauditor.models.finding import FindingStatus
from tests.conftest import make_finding


class TestAggregateSingleScope:
    def test_single_pass(self) -> None:
        findings = [make_finding(status=FindingStatus.PASS, scope=Scope.PROJECT)]
        results = aggregate(findings)
        assert len(results) == 1
        assert results[0].effective_status == FindingStatus.PASS

    def test_single_fail(self) -> None:
        findings = [make_finding(status=FindingStatus.FAIL, scope=Scope.PROJECT)]
        results = aggregate(findings)
        assert results[0].effective_status == FindingStatus.FAIL

    def test_single_skip_effective_fail(self) -> None:
        """A single SKIPPED finding means the setting is not configured → effective FAIL."""
        findings = [make_finding(status=FindingStatus.SKIPPED, scope=Scope.PROJECT)]
        results = aggregate(findings)
        assert results[0].effective_status == FindingStatus.FAIL

    def test_repository_scope_standalone(self) -> None:
        findings = [make_finding(status=FindingStatus.PASS, scope=Scope.REPOSITORY)]
        results = aggregate(findings)
        assert results[0].effective_status == FindingStatus.PASS
        assert results[0].scope_display[Scope.REPOSITORY] == FindingStatus.PASS.value


class TestAggregateMultiScope:
    def test_managed_pass_covers_lower_scopes(self) -> None:
        findings = [
            make_finding(status=FindingStatus.PASS, scope=Scope.MANAGED),
            make_finding(status=FindingStatus.SKIPPED, scope=Scope.PROJECT),
            make_finding(status=FindingStatus.SKIPPED, scope=Scope.USER),
        ]
        results = aggregate(findings)
        assert results[0].effective_status == FindingStatus.PASS
        assert results[0].scope_display[Scope.MANAGED] == FindingStatus.PASS.value
        assert results[0].scope_display[Scope.PROJECT] == COVERED
        assert results[0].scope_display[Scope.USER] == COVERED

    def test_project_pass_covers_user(self) -> None:
        findings = [
            make_finding(status=FindingStatus.SKIPPED, scope=Scope.MANAGED),
            make_finding(status=FindingStatus.PASS, scope=Scope.PROJECT),
            make_finding(status=FindingStatus.SKIPPED, scope=Scope.USER),
        ]
        results = aggregate(findings)
        assert results[0].effective_status == FindingStatus.PASS
        assert results[0].scope_display[Scope.PROJECT] == FindingStatus.PASS.value
        assert results[0].scope_display[Scope.USER] == COVERED

    def test_all_skipped_effective_fail(self) -> None:
        findings = [
            make_finding(status=FindingStatus.SKIPPED, scope=Scope.MANAGED),
            make_finding(status=FindingStatus.SKIPPED, scope=Scope.PROJECT),
            make_finding(status=FindingStatus.SKIPPED, scope=Scope.USER),
        ]
        results = aggregate(findings)
        assert results[0].effective_status == FindingStatus.FAIL
        # All scopes show their actual status (SKIPPED), none are COVERED
        assert results[0].scope_display[Scope.MANAGED] == FindingStatus.SKIPPED.value
        assert results[0].scope_display[Scope.PROJECT] == FindingStatus.SKIPPED.value
        assert results[0].scope_display[Scope.USER] == FindingStatus.SKIPPED.value

    def test_managed_fail_blocks_lower_scopes(self) -> None:
        """If managed is FAIL, lower scopes cannot override — effective is FAIL."""
        findings = [
            make_finding(status=FindingStatus.FAIL, scope=Scope.MANAGED),
            make_finding(status=FindingStatus.PASS, scope=Scope.PROJECT),
            make_finding(status=FindingStatus.PASS, scope=Scope.USER),
        ]
        results = aggregate(findings)
        assert results[0].effective_status == FindingStatus.FAIL
        # Managed is FAIL — lower scopes are NOT covered
        assert results[0].scope_display[Scope.MANAGED] == FindingStatus.FAIL.value

    def test_grouped_by_check_id(self) -> None:
        findings = [
            make_finding(check_id="CC001", scope=Scope.REPOSITORY),
            make_finding(check_id="CC002", scope=Scope.PROJECT),
            make_finding(check_id="CC002", scope=Scope.USER),
        ]
        results = aggregate(findings)
        assert len(results) == 2
        ids = [r.check_id for r in results]
        assert "CC001" in ids
        assert "CC002" in ids

    def test_severity_preserved(self) -> None:
        findings = [make_finding(severity=Severity.CRITICAL, scope=Scope.PROJECT)]
        results = aggregate(findings)
        assert results[0].severity == Severity.CRITICAL
