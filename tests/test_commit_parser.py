import pytest

from gh_cherry_pick.commit_parser import Commit


@pytest.mark.parametrize(
    "commit",
    ["2d55dd4", "2d55dd4a29e74aed8399b0fe4ba638370dd881d9"],
    ids=["short-sha", "long-sha"],
)
@pytest.mark.parametrize(
    ("input", "output"),
    [
        # user can use different separators
        ("repo/name/", ("repo", "name")),
        ("repo/name#", ("repo", "name")),
        ("repo/name@", ("repo", "name")),
    ],
    ids=["/", "#", "@"],
)
def test_commit_parser_separator(
    input: str, commit: str, output: tuple[str, str]
) -> None:
    assert Commit.parse(input + commit) == Commit(*output, commit)


def test_invalid_sha() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "^You have provided an invalid commit SHA1: 'sha@'\n"
            + "For repository foo/bar$"
        ),
    ):
        _ = Commit("foo", "bar", "sha@")


def test_repo_property() -> None:
    assert Commit("foo", "bar", "2d55dd4").repo == "foo/bar"


@pytest.mark.parametrize(
    "input",
    [
        "foo",
        "foo/",
        "foo,@bar",
        "foo/bar",
    ],
)
def test_invalid_input(input: str) -> None:
    with pytest.raises(
        ValueError,
        match=f"^Invalid commit reference provided: {input!r}\n"
        + "Must be in format: Owner/RepoName/commit$",
    ):
        _ = Commit.parse(input)
