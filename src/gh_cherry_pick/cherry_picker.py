import dataclasses
import typing as t

import httpx

from gh_cherry_pick.reference import Reference


@dataclasses.dataclass(frozen=True)
class CherryPicker:
    client: httpx.AsyncClient
    target: Reference

    async def cherry_pick_commit(self, commit: Reference) -> None:
        """Cherry pick one commit.

        This is built upon Jim's solution, which was written in pseudo-code
        https://stackoverflow.com/a/58672227/22235705. The comments from their
        solution are left in the same places, so it is easier to compare with
        the spec.
        """
        print(f"Cherry-picking {commit.repr} to {self.target.repr}...")
        commit_info = (
            (
                await self.client.get(
                    f"https://api.github.com/repos/{commit.repo}/commits/{commit.ref}"
                )
            )
            .raise_for_status()
            .json()
        )

        commit_message = self._prepare_commit_message(commit, commit_info)

        # Here is the branch we want to cherry-pick to:
        branch_info = (
            (
                await self.client.get(
                    f"https://api.github.com/repos/{self.target.repo}/branches/{self.target.ref}"
                )
            )
            .raise_for_status()
            .json()
        )
        branch_sha = branch_info["commit"]["sha"]
        branch_tree = branch_info["commit"]["commit"]["tree"]["sha"]

        # Create a temporary commit on the branch, which extends as a sibling of
        # the commit we want but contains the current tree of the target branch:
        parent_sha = commit_info["parents"][0]["sha"]
        if len(commit_info["parents"]) > 1:
            print(
                f"WARNING: Commit {commit.repr} has more than one parent, the "
                + "script may behave unnexpectably. Parents:"
                + "\n- ".join(parent["sha"] for parent in commit_info["parents"])
            )

        temp_commit = (
            (
                await self.client.post(
                    f"https://api.github.com/repos/{self.target.repo}/git/commits",
                    json={
                        "message": "temp",
                        "tree": branch_tree,
                        "parents": [parent_sha],
                    },
                )
            )
            .raise_for_status()
            .json()
        )

        # Now temporarily force the branch over to that commit
        _ = (
            await self.client.patch(
                f"https://api.github.com/repos/{self.target.repo}"
                + f"/git/refs/heads/{self.target.ref}",
                json={
                    "sha": temp_commit["sha"],
                    "force": True,
                },
            )
        ).raise_for_status()

        # Merge the commit we want into this mess:
        merge = (
            (
                await self.client.post(
                    f"https://api.github.com/repos/{self.target.repo}/merges",
                    json={
                        "base": self.target.ref,
                        "head": commit.ref,
                    },
                )
            )
            .raise_for_status()
            .json()
        )

        # and get that tree!
        merge_tree = merge["commit"]["tree"]["sha"]

        # Now that we know what the tree should be, create the cherry-pick commit.
        # Note that branchSha is the original from up at the top.
        cherry = (
            (
                await self.client.post(
                    f"https://api.github.com/repos/{self.target.repo}/git/commits",
                    json={
                        "message": commit_message,
                        "tree": merge_tree,
                        "parents": [branch_sha],
                    },
                )
            )
            .raise_for_status()
            .json()
        )

        # Replace the temp commit with the real commit:
        _ = (
            await self.client.patch(
                f"https://api.github.com/repos/{self.target.repo}"
                + f"/git/refs/heads/{self.target.ref}",
                json={"sha": cherry["sha"], "force": True},
            )
        ).raise_for_status()

        # Done!
        print(f"Successfully cherry-picked {commit.repr}!")

    def _prepare_commit_message(
        self, commit: Reference, commit_info: dict[str, t.Any]
    ) -> str:
        commit_message = commit_info["commit"]["message"]
        print(f"Message: {commit_message}")

        commit_message += f"\n\n(cherry-picked from commit {commit.ref})"
        commit_message += f"\n(from repository https://github.com/{commit.repo})"

        return commit_message

    async def hard_reset_target_to(self, commit: Reference) -> None:
        print(f"Hard resetting {self.target.repr} to {commit.repr}...")
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
