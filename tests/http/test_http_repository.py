from typing import Any, List

import httpx
import pytest

from generic_repository import HttpRepository, InvalidPayloadException

from .factories import TodoItemDataFactory
from .schemas import TodoItem

pytestmark = [
    pytest.mark.anyio(),
]


@pytest.fixture()
async def some_items(repo: HttpRepository, anyio_backend):
    return [
        await repo.add(payload) for payload in TodoItemDataFactory.create_batch(100)
    ]


@pytest.fixture()
async def item(repo: HttpRepository, anyio_backend):
    return TodoItem.parse_obj(await repo.add(TodoItemDataFactory.create()))


async def test_list_empty(repo: HttpRepository):
    items = await repo.get_list()
    assert len(items) == 0  # nosec assert_used


async def test_list(some_items: List[Any], repo: HttpRepository):
    result = await repo.get_list()
    assert len(result) == len(some_items)  # nosec: assert_used


@pytest.mark.parametrize(
    "bad_payload",
    (
        "a string",
        ["a", "list"],
        TodoItemDataFactory.create(title=None, body="A bad title."),
    ),
)
async def test_send_invalid(repo: HttpRepository, bad_payload: Any):
    with pytest.raises(InvalidPayloadException):
        await repo.add(bad_payload)


async def test_raises_httpx_exception(repo: HttpRepository):
    with pytest.raises(httpx.HTTPStatusError):
        await repo.get_list(params=dict(status_code=500))


async def test_remove(item: TodoItem, repo: HttpRepository):
    await repo.remove(str(item.id))
