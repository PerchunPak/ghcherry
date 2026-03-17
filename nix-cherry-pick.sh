#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

show-help() {
  cat <<EOF
nix-cherry-pick.sh - Cherry-pick commits to a flake.nix input

USAGE:
  nix-cherry-pick.sh [OPTIONS] <commits>

ARGUMENTS:
  <commits>             Commits to cherry-pick

OPTIONS:
  -s, --source <name>   Source input name, which will be used as a base branch
  -t, --target <name>   Target input name, to which the end result will be pushed
  -h, --help            Show this help message and exit

EXAMPLE:
  GITHUB_TOKEN=ght_... nix-cherry-pick.sh \\
    --source nixpkgs-upstream \\
    --target nixpkgs \\
    3f5ba52cc4701bf341457dfe5f6cb58e0cbb7f83 \\
    49ba75edefc8dc4fee45482f77a280ddd7121797 \\
    872811dce3bb220f53de549df3f522d709c33725

NOTE:
  Github token is required, specify it using \$GITHUB_TOKEN environment variable
EOF
}

function curl-gh {
  curl -sL \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "X-GitHub-Api-Version: 2026-03-10" \
    "$@"
}

function read-flake-lock {
  local meta=$(nix flake metadata --json)

  lock_version=$(echo "$meta" | jq -j .locks.version)
  if [ "$lock_version" -ne 7 ]; then
    echo "WARNING: expected lock version 7 but got $lock_version" >&2
  fi

  echo -n "$meta"
}

# get attribute from flake.lock for a specific input
# this is a separate function, so I don't have to duplicate the error message
function get-flake-input-attr {
  local flake_lock="$1" input="$2" attr="$3" result
  result=$(echo "$flake_lock" | jq -r ".locks.nodes.\"$input\".$attr")
  if [ "$result" = "null" ]; then
    echo "Input $input does not exist, check your flake.nix" >&2
    exit 1
  fi
  echo "$result"
}

function main() {
  local commits=() source_input target_input

  while [[ $# -gt 0 ]]; do
    case $1 in
      -h|--help)
        show-help
        exit 0
        ;;
      -s|--source)
        source_input="$2"
        shift # past argument
        shift # past value
        ;;
      -t|--target)
        target_input="$2"
        shift # past argument
        shift # past value
        ;;
      -*)
        echo "Unknown option $1"
        exit 1
        ;;
      *)
        commits+=("$1")
        shift
        ;;
    esac
  done

  if [ -z ${GITHUB_TOKEN+x} ]; then
    echo '$GITHUB_TOKEN is required, set it as an environment variable'
    echo ""
    show-help
    exit 1
  fi
  if [ -z ${source_input+x} ]; then
    echo "specify source input name using --source"
    echo "(input name is inputs.\${input_name}, e.g. inputs.nixpkgs would be --source nixpkgs)"
    echo "See also --help"
    exit 1
  fi
  if [ -z ${target_input+x} ]; then
    echo "specify target input name using --target"
    echo "(input name is inputs.\${input_name}, e.g. inputs.nixpkgs would be --target nixpkgs)"
    echo "See also --help"
    exit 1
  fi
  if [ ${#commits[@]} -eq 0 ]; then
    echo "Specify commits to cherry-pick as positional arguments, see --help"
    exit 1
  fi
  if [ ! -f flake.nix ] || [ ! -f flake.lock ]; then
    echo "flake.nix or flake.lock do not exist in the current directory"
    exit 1
  fi

  echo "Cherry-picking ${#commits[@]} commits, from input $source_input to input $target_input. Commits:"
  for commit in "${commits[@]}"; do
    echo "  $commit"
  done

  local flake_lock source_rev
  flake_lock=$(read-flake-lock)
  source_rev=$(get-flake-input-attr "$flake_lock" "$source_input" locked.rev)
  target_branch=$(get-flake-input-attr "$flake_lock" "$source_input" original.ref)

  echo "Source rev: $source_rev"
  echo "Target branch: $target_branch"
}

main "$@"
