"""Tests for the file_content checker."""

import pytest

from clauditor.checkers.file_content import FileContentChecker
from clauditor.models.check import CheckType, Scope
from clauditor.models.finding import FindingStatus
from tests.conftest import FILES_FIXTURES_DIR, StubProvider, make_check

CODEOWNERS_CHECK_CONFIG = {
    "search_paths": ["CODEOWNERS", ".github/CODEOWNERS"],
    "required_entries": [
        {"pattern": "/.claude/", "owner": "@security-team"},
        {"pattern": "/CLAUDE.md", "owner": "@security-team"},
    ],
}


@pytest.fixture
def checker() -> FileContentChecker:
    return FileContentChecker()


def _codeowners(filename: str) -> str:
    return (FILES_FIXTURES_DIR / filename).read_text()


class TestFileContentCheckerPass:
    def test_all_entries_present(self, checker: FileContentChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_CONTENT,
            check_config=CODEOWNERS_CHECK_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(
            scope=Scope.REPOSITORY,
            files={"CODEOWNERS": _codeowners("CODEOWNERS_complete")},
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS

    def test_fallback_to_second_search_path(self, checker: FileContentChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_CONTENT,
            check_config=CODEOWNERS_CHECK_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(
            scope=Scope.REPOSITORY,
            files={".github/CODEOWNERS": _codeowners("CODEOWNERS_complete")},
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS
        assert ".github/CODEOWNERS" in finding.target

    def test_comments_and_blank_lines_ignored(self, checker: FileContentChecker) -> None:
        content = "# comment\n\n/.claude/ @security-team\n/CLAUDE.md @security-team\n"
        check = make_check(
            check_type=CheckType.FILE_CONTENT,
            check_config=CODEOWNERS_CHECK_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(scope=Scope.REPOSITORY, files={"CODEOWNERS": content})
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS

    def test_no_owner_required(self, checker: FileContentChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_CONTENT,
            check_config={
                "search_paths": ["CODEOWNERS"],
                "required_entries": [{"pattern": "/.claude/"}],
            },
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(
            scope=Scope.REPOSITORY,
            files={"CODEOWNERS": "/.claude/ @anyone\n"},
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS


class TestFileContentCheckerFail:
    def test_file_not_found(self, checker: FileContentChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_CONTENT,
            check_config=CODEOWNERS_CHECK_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(scope=Scope.REPOSITORY, files={})
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.FAIL
        assert "No file found" in finding.message

    def test_missing_entry(self, checker: FileContentChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_CONTENT,
            check_config=CODEOWNERS_CHECK_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(
            scope=Scope.REPOSITORY,
            files={"CODEOWNERS": _codeowners("CODEOWNERS_partial")},
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.FAIL
        assert "/CLAUDE.md" in finding.message

    def test_wrong_owner(self, checker: FileContentChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_CONTENT,
            check_config=CODEOWNERS_CHECK_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(
            scope=Scope.REPOSITORY,
            files={"CODEOWNERS": _codeowners("CODEOWNERS_wrong_owner")},
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.FAIL
