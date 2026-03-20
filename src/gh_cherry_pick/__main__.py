import os
import typing as t

import cyclopts
import httpx

from gh_cherry_pick.cherry_picker import CherryPicker
from gh_cherry_pick.commit_parser import Commit
from gh_cherry_pick.logs import setup_logging
from gh_cherry_pick.target_info import Target

app = cyclopts.App(name="gh-cherry-pick", version_flags=[], backend="trio")


@app.meta.default
def callback(
    *_: t.Annotated[
        str, cyclopts.Parameter(show=False, allow_leading_hyphen=True)
    ],
) -> None:
    setup_logging()

    app()


@app.default
async def main(
    *commits: t.Annotated[
        Commit,
        cyclopts.Parameter(
            help="Commits to cherry-pick; format: Owner/RepoName/commit",
            required=True,
            converter=Commit.parse_cyclopts,
            n_tokens=1,
        ),
    ],
    target: t.Annotated[
        Target,
        cyclopts.Parameter(
            help=(
                "Target to where apply cherry-picks; format Owner/RepoName@branch"
            ),
            required=True,
            converter=Target.parse_cyclopts,
            n_tokens=1,
            accepts_keys=False,
        ),
    ],
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
    if not github_token:
        github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError(
            "You need to specify GitHub token either using --token "
            + "parameter or $GITHUB_TOKEN environment variable"
        )

    async with httpx.AsyncClient(
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }
    ) as session:
        cherry_picker = CherryPicker(session, target)
        for commit in commits:
            await cherry_picker.cherry_pick_commit(commit)


if __name__ == "__main__":
    app.meta()
