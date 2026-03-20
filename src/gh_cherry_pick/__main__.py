import os
import typing as t

import cyclopts

app = cyclopts.App(name="gh-cherry-pick", version_flags=[], backend="trio")


@app.default
async def main(
    *commits: t.Annotated[
        str,
        cyclopts.Parameter(help="Commits to cherry-pick", required=True),
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
