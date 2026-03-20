from typing import TYPE_CHECKING

import cyclopts.utils
import pytest

from gh_cherry_pick.commit_parser import Commit

if TYPE_CHECKING:
    import pytest_mock


@pytest.mark.parametrize(
    ("input", "output"),
    [
        ("repo/name/2d55dd4", ("repo", "name", "2d55dd4")),
        (
            "repo/name/2d55dd4a29e74aed8399b0fe4ba638370dd881d9",
            ("repo", "name", "2d55dd4a29e74aed8399b0fe4ba638370dd881d9"),
        ),
    ],
    ids=["short-sha", "long-sha"],
)
def test_commit_parser(input: str, output: tuple[str, str, str]) -> None:
    assert Commit.parse(input) == Commit(*output)


def test_invalid_sha() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "^You have provided an invalid commit SHA1: 'sha@'\n"
            + "For repository foo/bar$"
        ),
    ):
        _ = Commit("foo", "bar", "sha@")


@pytest.mark.parametrize(
    "input",
    [
        "foo",
        "foo/",
        "foo,@bar",
        "foo/bar",
        "foo/bar@baz",
    ],
)
def test_invalid_input(input: str) -> None:
    with pytest.raises(
        ValueError,
        match=f"^Invalid reference provided: {input!r}\n"
        + "Must be in format: Owner/RepoName/commit$",
    ):
        _ = Commit.parse(input)


def test_repo_property() -> None:
    assert Commit("foo", "bar", "2d55dd4").repo == "foo/bar"


def test_commit_repr_property() -> None:
    assert Commit("foo", "bar", "2d55dd4").repr == "foo/bar/2d55dd4"


def test_parse_cyclopts(mocker: pytest_mock.MockerFixture) -> None:
    mock = mocker.patch.object(Commit, "parse")
    assert (
        Commit.parse_cyclopts(
            (
                cyclopts.Token(
                    keyword=None,
                    value="PerchunPak/nixpkgs/e74327a46103e9b01f2951b8cdb4924ecb704465",
                    source="cli",
                    index=0,
                    keys=(),
                    implicit_value=cyclopts.utils.UNSET,
                ),
            ),
        )
        == mock.return_value
    )
    mock.assert_called_once_with(
        "PerchunPak/nixpkgs/e74327a46103e9b01f2951b8cdb4924ecb704465"
    )
