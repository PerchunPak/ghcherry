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
        commit.assert_is("commit", meta="commit to cherry-pick")
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

        commit_message += f"\n\n(cherry-picked from commit {commit.ref})"
        commit_message += f"\n(from repository https://github.com/{commit.repo})"

        return commit_message

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

    async def get_pr_commits(
        self, pr: Reference, *, commit_limit: int
    ) -> list[Reference]:
        print(f"Fetching {pr.repr} commits...")
        pr.assert_is("pr", meta="pull request number")

        commits: list[dict[str, t.Any]] = []
        for page in range(1, 4):
            batch: list[dict[str, t.Any]] = (
                (
                    await self.client.get(
                        f"https://api.github.com/repos/{pr.repo}"
                        + f"/pulls/{pr.ref}/commits"
                        + f"?per_page=100&page={page}",
                    )
                )
                .raise_for_status()
                .json()
            )
            commits.extend(batch)

            if len(commits) >= commit_limit:
                raise RuntimeError(
                    f"Pull request {pr.repr} contains more commits "
                    + f"({len(commits)}) than the specified limit "
                    + f"({commit_limit}). See `--pr-commits-limit` option\n"
                    + "\n"
                    + "This is a problem, because we cherry-pick each pull "
                    + "request commit instead of merging it. So you may "
                    + "accidentally end up cherry-picking hundreds of commits, "
                    + "without expecting it"
                )
            if len(batch) < 100:
                break

        commits_parsed: list[Reference] = []
        for commit in commits:
            # better safe than sorry
            commit_url = t.cast("str", commit["commit"]["url"])
            commit_url = commit_url.removeprefix("https://api.github.com/repos/")
            repo_owner, repo_name, *_ = commit_url.split("/")

            commits_parsed.append(
                Reference(
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    ref=commit["sha"],
                    ref_type="commit",
                )
            )

        print(f"Fetched {len(commits_parsed)} for {pr.ref}")
        return commits_parsed
