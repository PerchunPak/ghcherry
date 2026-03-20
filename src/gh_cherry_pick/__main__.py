import os
import typing as t

import cyclopts

from gh_cherry_pick.commit_parser import Commit, Target

app = cyclopts.App(name="gh-cherry-pick", version_flags=[], backend="trio")


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
            help="Target to where apply cherry-picks; format Owner/RepoName/commit",
            required=True,
            converter=Target.parse_cyclopts,
            n_tokens=1,
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


if __name__ == "__main__":
    app()
