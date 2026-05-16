import typing as t

import httpx
import pytest
from faker import Faker
from pytest_httpx import HTTPXMock

from ghcherry.logic._pr import PRApiClient
from ghcherry.reference import Reference


def gen_commit(sha: str) -> dict[str, t.Any]:
    return {
        "commit": {
            "url": "https://api.github.com/repos/aaa/bbb/ofkeo/feokfeo/feoekof/feofkeo",
        },
        "sha": sha,
    }


@pytest.mark.parametrize("amount_of_commits", [3, 250])
async def test_get_pr_commits(
    amount_of_commits: int, faker: Faker, httpx_mock: HTTPXMock
) -> None:
    commits = [faker.sha1() for _ in range(amount_of_commits)]
    for page in range(1, 4):
        page_commits = commits[100 * (page - 1) : 100 * page]
        if len(page_commits) == 0:
            break
        httpx_mock.add_response(
            url=f"https://api.github.com/repos/foo/bar/pulls/123/commits?per_page=100&page={page}",
            json=[gen_commit(commit) for commit in page_commits],
        )

    async with httpx.AsyncClient() as client:
        api = PRApiClient(client)
        assert await api.get_pr_commits(
            Reference.parse("foo/bar#123"),
            commit_limit=250,
        ) == [Reference.parse(f"aaa/bbb/{commit}") for commit in commits]


async def test_get_pr_commits_hit_limit(
    faker: Faker, httpx_mock: HTTPXMock
) -> None:
    commits = [faker.sha1() for _ in range(11)]
    httpx_mock.add_response(
        url="https://api.github.com/repos/foo/bar/pulls/123/commits?per_page=100&page=1",
        json=[gen_commit(commit) for commit in commits],
    )

    async with httpx.AsyncClient() as client:
        api = PRApiClient(client)
        with pytest.raises(
            RuntimeError,
            match=(
                r"^Pull request foo/bar#123 contains more commits \(11\) than "
                + r"the specified limit \(10\)"
            ),
        ):
            _ = await api.get_pr_commits(
                Reference.parse("foo/bar#123"),
                commit_limit=10,
            )
