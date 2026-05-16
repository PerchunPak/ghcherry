import dataclasses
import typing as t

from ghcherry.reference import Reference

from ._abc import AbstractAPIClient


@dataclasses.dataclass(frozen=True)
class PRApiClient(AbstractAPIClient):
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

            if len(commits) >= commit_limit and commit_limit != 250:
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

        print(f"Fetched {len(commits_parsed)} commits for {pr.repr}")
        return commits_parsed
