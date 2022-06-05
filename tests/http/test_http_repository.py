from typing import Any, List

import httpx
import pytest

from generic_repository import HttpRepository, InvalidPayloadException

from ..factories import TodoDataFactory
from ..todos import Todo

pytestmark = [
    pytest.mark.anyio(),
]


@pytest.fixture()
async def some_items(http_repository: HttpRepository, anyio_backend):
    return [
        await http_repository.add(payload)
        for payload in TodoDataFactory.create_batch(100)
    ]


@pytest.fixture()
async def item(http_repository: HttpRepository, anyio_backend):
    return Todo.parse_obj(await http_repository.add(TodoDataFactory.create()))


async def test_list_empty(http_repository: HttpRepository):
    items = await http_repository.get_list()
    assert len(items) == 0  # nosec assert_used


async def test_list(some_items: List[Any], http_repository: HttpRepository):
    result = await http_repository.get_list()
    assert len(result) == len(some_items)  # nosec: assert_used


@pytest.mark.parametrize(
    "bad_payload",
    (
        "a string",
        ["a", "list"],
        TodoDataFactory.create(title=None, body="A bad title."),
    ),
)
async def test_send_invalid(http_repository: HttpRepository, bad_payload: Any):
    with pytest.raises(InvalidPayloadException):
        await http_repository.add(bad_payload)


@pytest.mark.parametrize(
    "extra_data",
    ({"extra_1": 1}, {"extra_2": "str"}, "an str", 45),
)
@pytest.mark.parametrize(
    "payload",
    (pytest.param(TodoDataFactory(), marks=pytest.mark.xfail()), "an str", 45),
)
async def test_post_extra_data(
    http_repository: HttpRepository, payload: Any, extra_data: Any
):
    with pytest.raises(ValueError):
        await http_repository.add(payload, extra_data=extra_data)


async def test_raises_httpx_exception(http_repository: HttpRepository):
    with pytest.raises(httpx.HTTPStatusError):
        await http_repository.get_list(params=dict(status_code=500))
