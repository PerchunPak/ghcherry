import os
import typing as t

import cyclopts
import httpx

from gh_cherry_pick.cherry_picker import CherryPicker
from gh_cherry_pick.logs import setup_logging
from gh_cherry_pick.reference import Reference

app = cyclopts.App(name="gh-cherry-pick", version_flags=[], backend="trio")


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
            help="Target branch to where apply cherry-picks",
            required=True,
            converter=Reference.parse_cyclopts,
            n_tokens=1,
            accepts_keys=False,
        ),
    ],
    first_hard_reset_to: t.Annotated[
        Reference | None,
        cyclopts.Parameter(
            help="Before cherry-picking, hard reset target to this commit",
            required=False,
            converter=Reference.parse_cyclopts,
            n_tokens=1,
            accepts_keys=False,
        ),
    ] = None,
    github_token: t.Annotated[
        str | None,
        cyclopts.Parameter(
            name=["-t", "--token"],
            help=(
                "GitHub token, if not specified, fallbacks to the "
                + "$GITHUB_TOKEN environment variable"
            ),
        ),
    ] = None,
) -> None:
    """Cherry-pick commits across GitHub repositories using only the GitHub API.

    Branches are specified in format `Owner/RepoName@branch` and commits in
    `Owner/RepoName/commit`.

    You can specify branches instead of commits, and the script will merge them
    instead of cherry-picking. This is helpful if you want to maintain forked
    repository, but don't want to constantly update hashes.
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

    async with httpx.AsyncClient(
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }
    ) as session:
        cherry_picker = CherryPicker(session, target)
        if first_hard_reset_to:
            await cherry_picker.hard_reset_target_to(first_hard_reset_to)
        for ref in refs:
            if ref.ref_type == "commit":
                await cherry_picker.cherry_pick_commit(ref)
            else:
                await cherry_picker.merge_branch(ref)


if __name__ == "__main__":
    app.meta()
