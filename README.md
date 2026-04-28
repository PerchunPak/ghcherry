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
a fine-grained token with `contents` and `workflows` permissions.

If you want to cherry-pick commits in private repositories, the tool also
requires `Pull requests` permission for fine-grained tokens.

```bash
GITHUB_TOKEN=ghp_... gh-cherry-pick \
  --target MyOrg/nixpkgs@patched \
  `: # cherry-pick these commits` \
  NixOS/nixpkgs/3f5ba52cc4701bf341457dfe5f6cb58e0cbb7f83 \
  NixOS/nixpkgs/49ba75ed \
  `: # or merge the entire branch!` \
  Someone/nixpkgs@pr-branch \
  `: # or even cherry-pick every commit for a pull request!` \
  NixOS/nixpkgs#380691
```

### Arguments

You can give commits, branches and or pull requests as positional arguments.
Commits will be cherry-picked, while branches will be merged into the target.
For pull requests, we will collect PR's commits and add it to the list of
commits to cherry-pick.

Each commit/branch/PR is applied in order and builds upon the previous result.

- `--target`/`-T`: Required. Target branch to which to apply cherry-picks.
- `--first-hard-reset-to`/`-H`: Hard reset target to this commit, before doing
  anything else.
- `--pr-commits-limit`: If you specify PR to cherry-pick, this is the maximum
  amount of commits that the pull request can have.
- `--token`/`-t`: GitHub token. If not specified, falls back to the
  `$GITHUB_TOKEN` environment variable.

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

## Development

```bash
uv sync
uv run pre-commit install
```

Then commit your changes and send a pull request!
