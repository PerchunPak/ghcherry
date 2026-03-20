from __future__ import annotations

import abc
import re
import typing as t

import attrs

if t.TYPE_CHECKING:
    import cyclopts

SHA1_REGEX = re.compile(r"^\b[0-9a-f]{7,40}\b$")


def rev_is_sha(
    instance: Commit, _attribute: attrs.Attribute[str], value: str
) -> None:
    if not SHA1_REGEX.match(value):
        raise ValueError(
            f"You have provided an invalid commit SHA1: {value!r}\n"
            + f"For repository {instance.repo}"
        )


@attrs.define(frozen=True)
class Reference(abc.ABC):
    repo_owner: str
    repo_name: str

    trailing_key: t.ClassVar[str]

    @property
    def repo(self) -> str:
        return f"{self.repo_owner}/{self.repo_name}"

    @classmethod
    def parse(cls, input: str) -> t.Self:
        split_other_by: str
        if cls.trailing_key == "commit":
            split_other_by = "/"
        elif cls.trailing_key == "branch":
            split_other_by = "@"
        else:  # pragma: no cover
            raise RuntimeError(
                f"Class {cls} set unknown {cls.trailing_key=}. This is a bug"
            )

        error = ValueError(
            f"Invalid reference provided: {input!r}\n"
            + "Must be in format: Owner/RepoName"
            + f"{split_other_by}{cls.trailing_key}"
        )

        try:
            repo_owner, other = input.split("/", 1)
            repo_name, trailing_item = other.split(split_other_by, 1)
        except ValueError:
            raise error from None

        return cls(
            repo_owner,
            repo_name,
            trailing_item,  # pyright: ignore[reportCallIssue] # children have three fields
        )

    @classmethod
    def parse_cyclopts(cls, tokens: tuple[cyclopts.Token]) -> t.Self:
        return cls.parse(tokens[0].value)


@t.final
@attrs.define(frozen=True)
class Commit(Reference):
    repo_owner: str
    repo_name: str
    sha: str = attrs.field(validator=rev_is_sha)

    trailing_key = "commit"

    @property
    def repr(self) -> str:
        return f"{self.repo}/{self.sha}"
