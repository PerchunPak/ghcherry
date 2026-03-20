import typing as t

import attrs

from gh_cherry_pick.commit_parser import Reference


@t.final
@attrs.define(frozen=True)
class Target(Reference):
    branch: str

    trailing_key = "branch"

    @property
    def repr(self) -> str:
        return f"{self.repo}@{self.branch}"
