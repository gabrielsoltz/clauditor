"""Tests for the file_exists checker."""

import pytest

from clauditor.checkers.file_exists import FileExistsChecker
from clauditor.models.check import CheckType, Scope
from clauditor.models.finding import FindingStatus
from tests.conftest import StubProvider, make_check

MULTI_PATH_CONFIG = {
    "paths": ["CODEOWNERS", ".github/CODEOWNERS"],
    "any_of": False,
}

ANY_OF_CONFIG = {
    "paths": ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"],
    "any_of": True,
}


@pytest.fixture
def checker() -> FileExistsChecker:
    return FileExistsChecker()


class TestFileExistsCheckerPass:
    def test_all_files_present(self, checker: FileExistsChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_EXISTS,
            check_config=MULTI_PATH_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(
            scope=Scope.REPOSITORY,
            files={"CODEOWNERS": "content", ".github/CODEOWNERS": "content"},
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS

    def test_any_of_first_present(self, checker: FileExistsChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_EXISTS,
            check_config=ANY_OF_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(
            scope=Scope.REPOSITORY,
            files={"CODEOWNERS": "content"},
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS

    def test_any_of_last_present(self, checker: FileExistsChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_EXISTS,
            check_config=ANY_OF_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(
            scope=Scope.REPOSITORY,
            files={"docs/CODEOWNERS": "content"},
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS

    def test_single_required_file_present(self, checker: FileExistsChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_EXISTS,
            check_config={"paths": ["CLAUDE.md"], "any_of": False},
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(scope=Scope.REPOSITORY, files={"CLAUDE.md": "# Instructions"})
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.PASS


class TestFileExistsCheckerFail:
    def test_all_files_missing(self, checker: FileExistsChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_EXISTS,
            check_config=MULTI_PATH_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(scope=Scope.REPOSITORY, files={})
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.FAIL
        assert "CODEOWNERS" in finding.message

    def test_partial_files_missing_all_required(self, checker: FileExistsChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_EXISTS,
            check_config=MULTI_PATH_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(
            scope=Scope.REPOSITORY,
            files={"CODEOWNERS": "content"},  # only one of two required
        )
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.FAIL
        assert ".github/CODEOWNERS" in finding.message

    def test_any_of_none_present(self, checker: FileExistsChecker) -> None:
        check = make_check(
            check_type=CheckType.FILE_EXISTS,
            check_config=ANY_OF_CONFIG,
            scope=[Scope.REPOSITORY],
        )
        provider = StubProvider(scope=Scope.REPOSITORY, files={})
        finding = checker.run(check, provider)
        assert finding.status == FindingStatus.FAIL
        assert "None of the expected files" in finding.message
