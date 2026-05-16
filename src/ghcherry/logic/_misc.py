import dataclasses
import typing as t

from ghcherry.reference import Reference

from ._abc import AbstractAPIClient


@dataclasses.dataclass(frozen=True)
class MiscAPIClinent(AbstractAPIClient):
    target: Reference

    async def hard_reset_target_to(self, commit: Reference) -> None:
        print(f"Hard resetting {self.target.repr} to {commit.repr}...")
        if len(commit.ref) != 40:
            raise ValueError(
                "For `--first-hard-reset-to`, GitHub requires the full commit SHA"
            )

        _ = (
            await self.client.patch(
                f"https://api.github.com/repos/{self.target.repo}"
                + f"/git/refs/heads/{self.target.ref}",
                json={
                    "sha": commit.ref,
                    "force": True,
                },
            )
        ).raise_for_status()

    async def merge_branch(self, branch: Reference) -> None:
        branch.assert_is("branch", meta="branch to merge")
        print(f"Merging {branch.repr} into {self.target.repr}...")
        _ = (
            await self.client.post(
                f"https://api.github.com/repos/{self.target.repo}/merges",
                json={
                    "base": self.target.ref,
                    "head": branch.ref,
                },
            )
        ).raise_for_status()

    async def get_head_commit(self, branch: Reference) -> Reference:
        # using if instead of `assert_is` for better error message
        if branch.ref_type != "branch":
            raise ValueError(
                "You can get HEAD commit only on branches, "
                + f"but the function got {branch.repr}"
            )
        response = await self.client.get(
            f"https://api.github.com/repos/{branch.repo}/branches/{branch.ref}"
        )

        if response.status_code == 404:
            raise RuntimeError(
                "You tried to cherry-pick into a branch that "
                + f"doesn't exist ({branch.repr})"
            )
        _ = response.raise_for_status()

        json = response.json()

        # better safe than sorry
        commit_url = t.cast("str", json["commit"]["url"])
        commit_url = commit_url.removeprefix("https://api.github.com/repos/")
        repo_owner, repo_name, *_ = commit_url.split("/")

        return Reference(
            repo_owner=repo_owner,
            repo_name=repo_name,
            ref=json["commit"]["sha"],
            ref_type="commit",
        )
