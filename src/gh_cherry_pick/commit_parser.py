from __future__ import annotations

import abc
import re
import typing as t

import attrs
import cyclopts

GITHUB_REPO_REGEX = re.compile(r"^[\w\d.\-_]+")
SHA1_REGEX = re.compile(r"^\b[0-9a-f]{7,40}\b$")


@attrs.define(frozen=True)
class Reference(abc.ABC):
    repo_owner: str
    repo_name: str

    @property
    def repo(self) -> str:
        return f"{self.repo_owner}/{self.repo_name}"

    @classmethod
    def parse(cls, input: str) -> t.Self:
        error = ValueError(
            f"Invalid reference provided: {input!r}\n"
            + "Must be in format: Owner/RepoName/commit"
        )

        try:
            repo_owner, other = input.split("/", 1)
        except ValueError:
            raise error from None

        repo_name_match = GITHUB_REPO_REGEX.match(other)
        if repo_name_match is None:
            raise error

        repo_name = repo_name_match.group()
        trailing_item = other.removeprefix(repo_name)[1:]

        if not trailing_item:
            raise error

        return cls(
            repo_owner,
            repo_name,
            trailing_item,  # pyright: ignore[reportCallIssue] # children have three fields
        )

    @classmethod
    def parse_cyclopts(cls, tokens: tuple[cyclopts.Token]) -> t.Self:
        return cls.parse(tokens[0].value)


@attrs.define(frozen=True)
class Target(Reference):
    branch: str

    @property
    def repr(self) -> str:
        return f"{self.repo}/{self.branch}"


def rev_is_sha(
    instance: Commit, _attribute: attrs.Attribute[str], value: str
) -> None:
    if not SHA1_REGEX.match(value):
        raise ValueError(
            f"You have provided an invalid commit SHA1: {value!r}\n"
            + f"For repository {instance.repo}"
        )


@attrs.define(frozen=True)
class Commit(Reference):
    repo_owner: str
    repo_name: str
    sha: str = attrs.field(validator=rev_is_sha)

    @property
    def repr(self) -> str:
        return f"{self.repo}/{self.sha}"
