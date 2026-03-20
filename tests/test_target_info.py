from typing import TYPE_CHECKING

import cyclopts.utils
import pytest

from gh_cherry_pick.target_info import Target

if TYPE_CHECKING:
    import pytest_mock


def test_target_info() -> None:
    assert Target.parse("repo/name@foo") == Target("repo", "name", "foo")


@pytest.mark.parametrize(
    "input",
    [
        "foo",
        "foo/",
        "foo,@bar",
        "foo/bar",
        "foo/bar/baz",
    ],
)
def test_invalid_input(input: str) -> None:
    with pytest.raises(
        ValueError,
        match=f"^Invalid reference provided: {input!r}\n"
        + "Must be in format: Owner/RepoName@branch$",
    ):
        _ = Target.parse(input)


def test_repo_property() -> None:
    assert Target("foo", "bar", "baz").repo == "foo/bar"


def test_commit_repr_property() -> None:
    assert Target("foo", "bar", "baz").repr == "foo/bar@baz"


def test_parse_cyclopts(mocker: pytest_mock.MockerFixture) -> None:
    mock = mocker.patch.object(Target, "parse")
    assert (
        Target.parse_cyclopts(
            (
                cyclopts.Token(
                    keyword=None,
                    value="PerchunPak/nixpkgs@patched",
                    source="cli",
                    index=0,
                    keys=(),
                    implicit_value=cyclopts.utils.UNSET,
                ),
            ),
        )
        == mock.return_value
    )
    mock.assert_called_once_with("PerchunPak/nixpkgs@patched")
