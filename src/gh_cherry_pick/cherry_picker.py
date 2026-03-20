import typing as t

import attrs
import httpx

from gh_cherry_pick.commit_parser import Commit
from gh_cherry_pick.target_info import FetchedTarget


@attrs.frozen
class CherryPicker:
    client: httpx.AsyncClient
    target_info: FetchedTarget

    async def cherry_pick_commit(self, commit: Commit) -> None:
        target = self.target_info.meta
        print(f"Cherry-picking {commit.repr} to {target.repr}...")
        commit_info = (
            (
                await self.client.get(
                    f"https://api.github.com/repos/{commit.repo}/commits/{commit.sha}"
                )
            )
            .raise_for_status()
            .json()
        )

        commit_message = await self._prepare_commit_message(commit, commit_info)

        # Create a temporary commit on the branch, which extends as a sibling of
        # the commit we want but contains the current tree of the target branch:
        parent_sha = commit_info["parents"][0]["sha"]
        if len(commit_info["parents"]) > 1:
            print(
                f"WARNING: Commit {commit.repr} has more than one parent, the "
                + "script may behave unnexpectably"
            )

        temp_commit = (
            (
                await self.client.post(
                    f"https://api.github.com/repos/{target.repo}/git/commits",
                    json={
                        "message": "temp",
                        "tree": self.target_info.branch_tree,
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
                f"https://api.github.com/repos/{target.repo}"
                + f"/git/refs/heads/{target.branch}",
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
                    f"https://api.github.com/repos/{target.repo}/merges",
                    json={
                        "base": target.branch,
                        "head": commit.sha,
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
                    f"https://api.github.com/repos/{target.repo}/git/commits",
                    json={
                        "message": commit_message,
                        "tree": merge_tree,
                        "parents": [self.target_info.branch_sha],
                    },
                )
            )
            .raise_for_status()
            .json()
        )

        # Replace the temp commit with the real commit:
        _ = (
            await self.client.patch(
                f"https://api.github.com/repos/{target.repo}"
                + f"/git/refs/heads/{target.branch}",
                json={"sha": cherry["sha"], "force": True},
            )
        ).raise_for_status()

        # Done!
        print(f"Successfully cherry-picked {commit.repr}!")

    async def _prepare_commit_message(
        self, commit: Commit, commit_info: dict[str, t.Any]
    ) -> str:
        commit_message = commit_info["commit"]["message"]
        print(f"Message: {commit_message}")

        commit_message = commit_message.replace("\n", "\\n")
        commit_message += f"\n\n(cherry-picked from commit {commit.sha})"
        commit_message += f"\n(from repository https://github.com/{commit.repo})"

        return commit_message

    async def _make_api_request(
        self, method: str, url: str, **kwargs: t.Any
    ) -> dict[str, t.Any]:
        response = await getattr(self.client, method)(
            "https://api.github.com/" + url, **kwargs
        )
        return response.json()
