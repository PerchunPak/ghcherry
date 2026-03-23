import typing as t

import cyclopts.utils
import pytest
import pytest_mock

from gh_cherry_pick.reference import Reference


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
    assert Reference.parse(input) == Reference(*output, "commit")


def test_branch_parser() -> None:
    assert Reference.parse("repo/name@foo") == Reference(
        "repo", "name", "foo", ref_type="branch"
    )


@pytest.mark.parametrize(
    "input",
    [
        "foo",
        "foo/",
        "foo,@bar",
        "foo/bar",
        "foo/bar#baz",
    ],
)
def test_reference_invalid_input(input: str) -> None:
    with pytest.raises(
        ValueError,
        match=(
            f"^Invalid reference provided: {input!r}\n"
            + "Must be in format: Owner/RepoName/commit "
            + "or Owner/RepoName@branch$"
        ),
    ):
        _ = Reference.parse(input)


def test_commit_invalid_sha() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "^You have provided an invalid commit SHA1: 'sha@'\n"
            + r"\(full input foo/bar/sha@\)$"
        ),
    ):
        _ = Reference.parse("foo/bar/sha@")


@pytest.mark.parametrize("ref_type", ["commit", "branch"])
def test_repo_property(ref_type: t.Literal["commit", "branch"]) -> None:
    assert Reference("foo", "bar", "2d55dd4", ref_type).repo == "foo/bar"


def test_commit_repr_property() -> None:
    assert (
        Reference("foo", "bar", "2d55dd4", ref_type="commit").repr
        == "foo/bar/2d55dd4"
    )


def test_branch_repr_property() -> None:
    assert Reference("foo", "bar", "baz", ref_type="branch").repr == "foo/bar@baz"


@pytest.mark.parametrize("ref_type", ["commit", "branch"])
def test_parse_cyclopts(mocker: pytest_mock.MockerFixture, ref_type: str) -> None:
    mock = mocker.patch.object(Reference, "parse")
    sep = "/" if ref_type == "commit" else "@"
    assert (
        Reference.parse_cyclopts(
            (
                cyclopts.Token(
                    keyword=None,
                    value=f"PerchunPak/nixpkgs{sep}2d55dd4",
                    source="cli",
                    index=0,
                    keys=(),
                    implicit_value=cyclopts.utils.UNSET,
                ),
            ),
        )
        == mock.return_value
    )
    mock.assert_called_once_with(f"PerchunPak/nixpkgs{sep}2d55dd4")


@pytest.mark.parametrize("ref_type", ["commit", "branch"])
def test_assert_is_true(ref_type: str) -> None:
    sep = "/" if ref_type == "commit" else "@"
    ref = Reference.parse(f"PerchunPak/nixpkgs{sep}2d55dd4")
    # does not raise
    ref.assert_is(ref_type, meta="foo")


@pytest.mark.parametrize("ref_type", ["commit", "branch"])
def test_assert_is_false(ref_type: str) -> None:
    sep = "/" if ref_type == "commit" else "@"
    ref = Reference.parse(f"PerchunPak/nixpkgs{sep}2d55dd4")

    format = (
        "Owner/RepoName@branch"
        if ref_type == "commit"
        else "Owner/RepoName/commit"
    )
    with pytest.raises(
        ValueError,
        match=f"^Invalid foo provided: '2d55dd4'\nMust be in format: {format}$",
    ):
        ref.assert_is(
            "branch" if ref_type == "commit" else "commit",
            meta="foo",
        )
