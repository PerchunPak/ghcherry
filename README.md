# GitHub cherry-pick

Cherry-pick commits across GitHub repositories using only the GitHub API - no local clone required.

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

```
gh-cherry-pick --target OWNER/REPO@BRANCH COMMITS...
```

**Arguments:**

| Argument | Format | Description |
|---|---|---|
| `--target` | `Owner/RepoName@branch` | Target repository and branch to apply the cherry-picks to |
| `COMMITS` | `Owner/RepoName/sha` | One or more commits to cherry-pick (short or full SHA) |
| `--token`, `-t` | string | GitHub token (falls back to `$GITHUB_TOKEN`) |

**Example:**

```bash
GITHUB_TOKEN=ghp_... gh-cherry-pick \
  --target MyOrg/nixpkgs@patched \
  NixOS/nixpkgs/3f5ba52cc4701bf341457dfe5f6cb58e0cbb7f83 \
  NixOS/nixpkgs/49ba75edefc8dc4fee45482f77a280ddd7121797
```

Multiple commits are applied in order, each building on the previous result.

## Development

```bash
uv sync
uv run pre-commit install
```

Then commit your changes and send a pull request!
