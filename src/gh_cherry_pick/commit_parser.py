from __future__ import annotations

import re
import typing as t

import attrs

GITHUB_REPO_REGEX = re.compile(r"^[\w\d.\-_]+")
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
class Commit:
    repo_owner: str
    repo_name: str
    sha: str = attrs.field(validator=rev_is_sha)

    @property
    def repo(self) -> str:
        return f"{self.repo_owner}/{self.repo_name}"

    @classmethod
    def parse(cls, input: str) -> t.Self:
        repo_owner, other = input.split("/", 1)
        repo_name_match = GITHUB_REPO_REGEX.match(other)
        if repo_name_match is None:
            raise ValueError(
                f"Invalid commit reference provided: {input!r}\n"
                + "Must be in format: Owner/RepoName/commit"
            )
        repo_name = repo_name_match.group()
        commit = other.removeprefix(repo_name)[1:]

        return cls(
            repo_owner=repo_owner,
            repo_name=repo_name,
            sha=commit,
        )
