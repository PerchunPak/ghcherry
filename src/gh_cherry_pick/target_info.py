import typing as t

import attrs
import httpx

from gh_cherry_pick.commit_parser import Reference


@t.final
@attrs.define(frozen=True)
class Target(Reference):
    branch: str

    trailing_key = "branch"

    @property
    def repr(self) -> str:
        return f"{self.repo}@{self.branch}"


@attrs.define(frozen=True)
class FetchedTarget:
    meta: Target

    branch_sha: str
    branch_tree: str

    @classmethod
    async def fetch(cls, client: httpx.AsyncClient, meta: Target) -> t.Self:
        branch_info = (
            await client.get(
                f"https://api.github.com/repos/{meta.repo}/branches/{meta.branch}"
            )
        ).json()
        branch_sha = branch_info["commit"]["sha"]
        branch_tree = branch_info["commit"]["commit"]["tree"]["sha"]

        return cls(
            meta=meta,
            branch_sha=branch_sha,
            branch_tree=branch_tree,
        )
