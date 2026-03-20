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
