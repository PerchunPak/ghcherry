import typing as t

from ghcherry.logic._cherry_picker import CherryPicker
from ghcherry.reference import Reference


def test_prepare_commit_message() -> None:
    sha = "b295a55c83c36b5ad0c9a4cc058a71a3aa956d23"
    commit_info: dict[str, t.Any] = {
        "sha": sha,
        "commit": {
            "author": {
                "name": "r-vdp",
                "email": "ramses@well-founded.dev",
                "date": "2026-03-19T11:25:44Z",
            },
            "message": 'nixos/tests/systemd-homed: fix firstboot prompt flow for v259\n\nThe test has been broken since the 258.3 -> 259 bump. v259 removed the\n"Press any key to proceed" gate and changed the firstboot unit to pass\n--prompt-shell=no --prompt-groups=no, so the shell and group prompts\nthe test waits for never appear.\n\nUpdate to the current prompt sequence (username, password, repeat).\nAdd wheel membership via homectl update afterwards since the wizard no\nlonger prompts for groups. Leaving the shell unset also exercises the\nNixOS default-user-shell meson option.',  # noqa: E501
            "tree": {
                "sha": "af7c7abf89434789a8fb49773bc6cf38faab87d3",
                "url": "https://api.github.com/repos/PerchunPak/nixpkgs/git/trees/af7c7abf89434789a8fb49773bc6cf38faab87d3",
            },
        },
        "parents": [
            {
                "sha": "940bf1fb28da28b7655ef73efc8d60c31aeac17c",
                "url": "https://api.github.com/repos/PerchunPak/nixpkgs/commits/940bf1fb28da28b7655ef73efc8d60c31aeac17c",
                "html_url": "https://github.com/PerchunPak/nixpkgs/commit/940bf1fb28da28b7655ef73efc8d60c31aeac17c",
            }
        ],
    }
    commit = Reference("PerchunPak", "nixpkgs", ref=sha, ref_type="commit")
    target = Reference("PerchunPak", "nixpkgs", ref="patched", ref_type="branch")
    cherry_picker = CherryPicker(client=None, target=target)  # pyright: ignore[reportArgumentType]

    # ruff: disable[E501]
    assert cherry_picker._prepare_commit_message(commit, commit_info) == (
        "nixos/tests/systemd-homed: fix firstboot prompt flow for v259\n"
        + "\n"
        + "The test has been broken since the 258.3 -> 259 bump. v259 removed the\n"
        + '"Press any key to proceed" gate and changed the firstboot unit to pass\n'
        + "--prompt-shell=no --prompt-groups=no, so the shell and group prompts\n"
        + "the test waits for never appear.\n"
        + "\n"
        + "Update to the current prompt sequence (username, password, repeat).\n"
        + "Add wheel membership via homectl update afterwards since the wizard no\n"
        + "longer prompts for groups. Leaving the shell unset also exercises the\n"
        + "NixOS default-user-shell meson option."
        + f"\n\n(cherry-picked from commit {sha})"
        + "\n(from repository https://github.com/PerchunPak/nixpkgs)"
    )
    # ruff: enable[E501]
