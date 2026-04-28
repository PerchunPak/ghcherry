import os
import typing as t

import cyclopts
import httpx

from gh_cherry_pick.cherry_picker import CherryPicker
from gh_cherry_pick.logs import setup_logging
from gh_cherry_pick.reference import Reference

app = cyclopts.App(name="gh-cherry-pick")


@app.meta.default
def callback(
    *tokens: t.Annotated[
        str, cyclopts.Parameter(show=False, allow_leading_hyphen=True)
    ],
) -> None:
    setup_logging()

    app(tokens)


@app.default
async def main(
    *refs: t.Annotated[
        Reference,
        cyclopts.Parameter(
            help="Commits to cherry-pick or branches to merge",
            required=True,
            converter=Reference.parse_cyclopts,
            n_tokens=1,
        ),
    ],
    target: t.Annotated[
        Reference,
        cyclopts.Parameter(
            help="Target branch to which to apply cherry-picks",
            required=True,
            converter=Reference.parse_cyclopts,
            n_tokens=1,
            accepts_keys=False,
        ),
    ],
    first_hard_reset_to: t.Annotated[
        Reference | None,
        cyclopts.Parameter(
            help="Hard reset target to this commit, before doing anything else",
            required=False,
            converter=Reference.parse_cyclopts,
            n_tokens=1,
            accepts_keys=False,
        ),
    ] = None,
    pr_commits_limit: t.Annotated[
        int,
        cyclopts.Parameter(
            help=(
                "If you specify PR to cherry-pick, this is the maximum amount of "
                + "commits that the pull request can have"
            )
        ),
    ] = 30,
    github_token: t.Annotated[
        str | None,
        cyclopts.Parameter(
            name=["-t", "--token"],
            help=(
                "GitHub token. If not specified, falls back to the "
                + "$GITHUB_TOKEN environment variable"
            ),
        ),
    ] = None,
) -> None:
    """Cherry-pick commits across GitHub repositories using only the GitHub API.

    You can give commits, branches and or pull requests as positional
    arguments. Commits will be cherry-picked, while branches will be merged
    into the target. For pull requests, we will collect PR's commits and add it
    to the list of commits to cherry-pick.

    Each commit/branch/PR is applied in order and builds upon the previous
    result.

    ### Supported formats:

    For commits:
    - Owner/RepoName/commit
    - https://github.com/Owner/RepoName/commit/09588bb

    For branches:
    - Owner/RepoName@branch
    - https://github.com/Owner/RepoName/tree/branch

    For pull requests:
    - Owner/RepoName#123
    - https://github.com/Owner/RepoName/pull/123
    """
    if not github_token:
        github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError(
            "You need to specify GitHub token either using --token "
            + "parameter or $GITHUB_TOKEN environment variable"
        )
    target.assert_is("branch", meta="target")
    if first_hard_reset_to is not None:
        first_hard_reset_to.assert_is("commit", meta="--first-hard-reset-to")
    if pr_commits_limit > 250:
        raise ValueError(
            "--pr-commits-limit cannot be bigger than 250. "
            + "GitHub API can only return first 250 commits"
        )

    async with httpx.AsyncClient(
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }
    ) as session:
        cherry_picker = CherryPicker(session, target)
        original_commit = await cherry_picker.get_head_commit(target)

        refs_to_process: list[Reference] = []
        for ref in refs:
            if ref.ref_type != "pr":
                refs_to_process.append(ref)
                continue

            refs_to_process.extend(
                await cherry_picker.get_pr_commits(
                    ref, commit_limit=pr_commits_limit
                )
            )

        s = "s" if len(refs_to_process) > 1 else ""
        print(
            f"Cherry-picking {len(refs_to_process)} reference{s} to "
            + f"{target.repr} ({original_commit.ref[:7]}):"
        )
        print("\n".join(f"- {ref.repr}" for ref in refs_to_process))
        print()

        try:
            if first_hard_reset_to:
                await cherry_picker.hard_reset_target_to(first_hard_reset_to)
            for ref in refs_to_process:
                if ref.ref_type == "commit":
                    await cherry_picker.cherry_pick_commit(ref)
                else:
                    await cherry_picker.merge_branch(ref)
        except Exception:
            print(
                "\nFailed to cherry-pick commits, rolling back to the "
                + f"original commit ({original_commit.repr})"
            )
            await cherry_picker.hard_reset_target_to(original_commit)
            raise


if __name__ == "__main__":
    app.meta()
