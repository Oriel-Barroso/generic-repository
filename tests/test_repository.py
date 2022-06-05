import factory
import pytest

from generic_repository.exceptions import ItemNotFoundException

from .factories import AddTodoFactory
from .todos import Todo, TodoRepository, UpdateTodoPayload

pytestmark = [
    pytest.mark.anyio(),
]


@pytest.fixture()
async def items(repository: TodoRepository, anyio_backend):
    items = AddTodoFactory.create_batch(40)
    return [await repository.add(payload) for payload in items]


@pytest.fixture()
async def item(repository: TodoRepository, anyio_backend):
    item = AddTodoFactory.create()
    return await repository.add(item)


async def test_count(repository: TodoRepository, items: list[Todo]):
    count = await repository.get_count()
    assert count == len(items)  # nosec


async def test_list_without_size(items: list[Todo], repository: TodoRepository):
    result = await repository.get_list()
    assert len(result) == len(items)  # nosec


async def test_list_with_size(items: list[Todo], repository: TodoRepository):
    result = await repository.get_list(size=10)
    assert len(result) == 10  # nosec


@pytest.mark.xfail()
async def test_list_with_offset(items: list[Todo], repository: TodoRepository):
    result = await repository.get_list(offset=10)

    assert len(result) == len(items) - 10  # nosec


async def test_get_nonexistent(repository: TodoRepository):
    with pytest.raises(ItemNotFoundException):
        await repository.get_by_id(100)


async def test_get_existing(repository: TodoRepository, item: Todo):
    result = await repository.get_by_id(item.id)  # type: ignore
    assert result.id == item.id  # nosec


async def test_delete_existing(repository: TodoRepository, item: Todo):
    await repository.remove(item.id)  # type: ignore


async def test_delete_nonexistent(repository: TodoRepository):
    with pytest.raises(ItemNotFoundException):
        await repository.remove(100)


async def test_create(repository: TodoRepository):
    payload = AddTodoFactory.create()
    result = await repository.add(payload)
    assert result.id is not None  # nosec


async def test_update(repository: TodoRepository, item: Todo):
    payload = factory.build(UpdateTodoPayload, title=factory.Faker("word"))
    assert item.id  # nosec
    result = await repository.update(item.id, payload)
    assert result.title == payload.title  # nosec


async def test_replace(repository: TodoRepository, item: Todo):
    payload = AddTodoFactory.build()
    assert item.id  # nosec
    result = await repository.replace(item.id, payload)
    assert result.title == payload.title  # nosec
