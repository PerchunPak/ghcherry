# GitHub cherry-pick

Cherry-pick commits across GitHub repositories using only the GitHub API.

## How it works

Uses the algorithm described by [Jim's Stack Overflow
answer](https://stackoverflow.com/a/58672227/22235705) to perform a cherry-pick
entirely through the GitHub REST API:

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

```bash
GITHUB_TOKEN=ghp_... gh-cherry-pick \
  --target MyOrg/nixpkgs@patched \
  NixOS/nixpkgs/3f5ba52cc4701bf341457dfe5f6cb58e0cbb7f83 \
  NixOS/nixpkgs/49ba75edefc8dc4fee45482f77a280ddd7121797 \
  Someone/nixpkgs@pr-branch
```

### Arguments

You can give commits and/or branches as positional arguments. Commits will be
cherry-picked, while branches will be merged into target. Each commit/branch is
applied in order and builds on previous result.

### Parameters

Format for branches is `Owner/Repo@branch` and for commits is `Owner/Repo/commit`.

- `--target`: Required. Target branch to where apply cherry-picks.
- `--first-hard-reset-to`: Hard reset target to this commit, before doing
  anything else.
- `--token`/`-t`: GitHub token. If not specified, fallbacks to the
  `$GITHUB_TOKEN` environment variable.

## Development

```bash
uv sync
uv run pre-commit install
```

Then commit your changes and send a pull request!
