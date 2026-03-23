from __future__ import annotations

import abc
import re
import typing as t

import attrs
import typing_extensions as te

if t.TYPE_CHECKING:
    import cyclopts

SHA1_REGEX = re.compile(r"^\b[0-9a-f]{7,40}\b$")
GITHUB_REPO_REGEX = re.compile(r"^[\w\d.\-_]+")


@attrs.define(frozen=True)
class Reference(abc.ABC):
    repo_owner: str
    repo_name: str

    ref: str
    ref_type: t.Literal["branch", "commit"]

    @property
    def repo(self) -> str:
        return f"{self.repo_owner}/{self.repo_name}"

    @property
    def repr(self) -> str:
        separator = "/" if self.ref_type == "commit" else "@"
        return self.repo + separator + self.ref

    @classmethod
    def parse(cls, input: str) -> te.Self:
        error = ValueError(
            f"Invalid reference provided: {input!r}\n"
            + "Must be in format: Owner/RepoName/commit "
            + "or Owner/RepoName@branch"
        )

        try:
            repo_owner, other = input.split("/", 1)
        except ValueError:
            raise error from None

        repo_name_match = GITHUB_REPO_REGEX.match(other)
        if repo_name_match is None:
            raise error

        repo_name = repo_name_match.group()
        trailing_item = other.removeprefix(repo_name)
        if not trailing_item:
            raise error
        separator, ref = trailing_item[0], trailing_item[1:]

        if separator not in ("/", "@"):
            raise error
        ref_type = "commit" if separator == "/" else "branch"

        if ref_type == "commit" and not SHA1_REGEX.match(ref):
            raise ValueError(
                f"You have provided an invalid commit SHA1: {ref!r}\n"
                + f"(full input {input})"
            )

        return cls(
            repo_name=repo_name,
            repo_owner=repo_owner,
            ref=ref,
            ref_type=ref_type,
        )

    @classmethod
    def parse_cyclopts(cls, tokens: tuple[cyclopts.Token]) -> te.Self:
        return cls.parse(tokens[0].value)

    def assert_is(self, ref_type: str, *, meta: str) -> None:
        if ref_type == "branch":
            format = "Owner/RepoName@branch"
        else:
            format = "Owner/RepoName/commit"

        if self.ref_type != ref_type:
            raise ValueError(
                f"Invalid {meta} provided: {self.ref!r}\n"
                + f"Must be in format: {format}"
            )
