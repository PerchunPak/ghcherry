from __future__ import annotations

import dataclasses
import re
import typing as t

if t.TYPE_CHECKING:
    import cyclopts
    import typing_extensions as te

SHA1_REGEX = re.compile(r"^\b[0-9a-f]{7,40}\b$")
GITHUB_REPO_REGEX = re.compile(r"^[\w\d.\-_]+")

SEPARATOR_TO_REF_TYPE = {
    "/": "commit",
    "@": "branch",
    "#": "pr",
}
REF_TYPE_TO_SEPARATOR = {v: k for k, v in SEPARATOR_TO_REF_TYPE.items()}


@dataclasses.dataclass(frozen=True)
class Reference:
    repo_owner: str
    repo_name: str

    ref: str
    ref_type: t.Literal["commit", "branch", "pr"]

    @property
    def repo(self) -> str:
        return f"{self.repo_owner}/{self.repo_name}"

    @property
    def repr(self) -> str:
        separator = REF_TYPE_TO_SEPARATOR[self.ref_type]
        return self.repo + separator + self.ref

    @classmethod
    def parse(cls, input: str) -> te.Self:
        error = ValueError(
            f"Invalid reference provided: {input!r}\n"
            + "Supported formats:\n"
            + "- Owner/RepoName/commit\n"
            + "- Owner/RepoName@branch\n"
            + "- Owner/RepoName#pr-number\n"
            + "- https://github.com/Owner/RepoName/commit/09588bb\n"
            + "- https://github.com/Owner/RepoName/tree/branch\n"
            + "- https://github.com/Owner/RepoName/pull/123"
        )

        if input.startswith("https://github.com/"):
            input = input.removeprefix("https://github.com/")
            input = input.replace("/commit/", "/")
            input = input.replace("/tree/", "@")
            input = input.replace("/pull/", "#")

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

        if separator not in ("/", "@", "#"):
            raise error
        ref_type = SEPARATOR_TO_REF_TYPE[separator]

        if ref_type == "commit" and not SHA1_REGEX.match(ref):
            raise ValueError(
                f"You have provided an invalid commit SHA1: {ref!r}\n"
                + f"(full input {input})"
            )
        if ref_type == "pr" and not ref.isdigit():
            raise ValueError(
                f"You have provided an invalid pull request number: {ref!r}\n"
                + f"(full input {input})"
            )

        return cls(
            repo_name=repo_name,
            repo_owner=repo_owner,
            ref=ref,
            ref_type=ref_type,  # pyright: ignore[reportArgumentType] # str != literal
        )

    @classmethod
    def parse_cyclopts(cls, tokens: tuple[cyclopts.Token]) -> te.Self:
        return cls.parse(tokens[0].value)

    def assert_is(self, ref_type: str, *, meta: str) -> None:
        if ref_type == "commit":
            format = "Owner/RepoName/commit"
        elif ref_type == "branch":
            format = "Owner/RepoName@branch"
        else:
            format = "Owner/RepoName#123"

        if self.ref_type != ref_type:
            raise ValueError(
                f"Invalid {meta} provided: {self.ref!r}\n"
                + f"Must be in format: {format}"
            )
