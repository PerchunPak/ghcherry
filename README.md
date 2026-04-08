# GitHub cherry-pick

Cherry-pick commits across GitHub repositories using only the GitHub API.

Uses the algorithm described by [Jim's Stack Overflow
answer](https://stackoverflow.com/a/58672227/22235705) to perform a cherry-pick
entirely through the GitHub REST API. This is much better than doing that
through patches (e.g. [`patch2pr`](https://github.com/bluekeyes/patch2pr)),
because git is much smarter with resolving conflicts on commits instead of
patches.

When I used patch2pr, I had to constantly rebase my patches, because on almost
every update they would raise conflicts. Cherry-picking those commits works
perfectly fine!

## Installation

Requires Python 3.10+, I recommend using [uv](https://docs.astral.sh/uv/), but
it will work fine with pip or anything else.

```bash
uv tool install gh-cherry-pick
```

Or run directly without installing:

```bash
uvx gh-cherry-pick --help
```

## Usage

This tool requires a classic token with `repo` and `workflow` permissions
(`workflow` is needed only if commits update `.github/workflows` files) or
fine-grained token with `contents` and `workflows` permissions.

```bash
GITHUB_TOKEN=ghp_... gh-cherry-pick \
  --target MyOrg/nixpkgs@patched \
  `: # cherry-pick these commits` \
  NixOS/nixpkgs/3f5ba52cc4701bf341457dfe5f6cb58e0cbb7f83 \
  NixOS/nixpkgs/49ba75edefc8dc4fee45482f77a280ddd7121797 \
  `: # or merge the entire branch!` \
  Someone/nixpkgs@pr-branch
```

### Arguments

You can give commits and/or branches as positional arguments. Commits will be
cherry-picked, while branches will be merged into the target. Each
commit/branch is applied in order and builds on the previous result.

Format for branches is `Owner/Repo@branch` and for commits is
`Owner/Repo/commit`.

- `--target`: Required. Target branch to which to apply cherry-picks.
- `--first-hard-reset-to`: Hard reset target to this commit, before doing
  anything else.
- `--token`/`-t`: GitHub token. If not specified, falls back to the
  `$GITHUB_TOKEN` environment variable.

## Development

```bash
uv sync
uv run pre-commit install
```

Then commit your changes and send a pull request!
