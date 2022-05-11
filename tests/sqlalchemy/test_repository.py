import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from generic_repository.exceptions import ItemNotFoundException

from .factories import AddTodoFactory, TodoItemModelFactory
from .models import TodoItem
from .repository import TodoRepository

pytestmark = [
    pytest.mark.anyio(),
]


@pytest.fixture()
async def items(db_session: AsyncSession):
    items = TodoItemModelFactory.create_batch(40)
    async with db_session.begin_nested() as savepoint:
        async with db_session.begin_nested():
            db_session.add_all(items)

        try:
            yield items
        finally:
            await savepoint.rollback()


@pytest.fixture()
async def item(db_session: AsyncSession):
    async with db_session.begin_nested() as savepoint:
        item = TodoItemModelFactory()
        async with db_session.begin_nested():
            db_session.add(item)

        try:
            yield item
        finally:
            await savepoint.rollback()


async def test_count(
    db_session: AsyncSession, repository: TodoRepository, items: list[TodoItem]
):
    count = await repository.get_count()
    assert count == len(items)


async def test_list_without_size(items: list[TodoItem], repository: TodoRepository):
    result = await repository.get_list()
    assert len(result) == len(items)


async def test_list_with_size(items: list[TodoItem], repository: TodoRepository):
    result = await repository.get_list(size=10)
    assert len(result) == 10


async def test_get_nonexistent(repository: TodoRepository):
    with pytest.raises(ItemNotFoundException):
        await repository.get_by_id(100)


async def test_get_existing(repository: TodoRepository, item: TodoItem):
    result = await repository.get_by_id(item.id)  # type: ignore
    assert result.id == item.id


async def test_delete_existing(repository: TodoRepository, item: TodoItem):
    await repository.remove(item.id)  # type: ignore


async def test_delete_nonexistent(repository: TodoRepository):
    with pytest.raises(ItemNotFoundException):
        await repository.remove(100)


async def test_create(repository: TodoRepository):
    payload = AddTodoFactory()
    result = await repository.add(payload)
    assert result.id is not None
