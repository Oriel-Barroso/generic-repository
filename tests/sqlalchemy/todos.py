# pylint: disable=import-error
"""
Todos database implementation.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from generic_repository import (
    ConstructorMapper,
    DatabaseRepository,
    PydanticDictMapper,
    PydanticObjectMapper,
    ToFunctionArgsMapper,
)

from ..todos import AddTodoPayload, Todo, TodoRepository, UpdateTodoPayload
from .models import TodoItem


class DbTodoRepository(
    DatabaseRepository[
        TodoItem, AddTodoPayload, UpdateTodoPayload, AddTodoPayload, Todo, int
    ],
    TodoRepository,
):
    """The todo item database repository."""

    model_class = TodoItem
    primary_key_column = model_class.id  # type: ignore

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session=session,
            item_mapper=PydanticObjectMapper(Todo),
            create_mapper=PydanticDictMapper(AddTodoPayload)
            .chain(ToFunctionArgsMapper())
            .chain(ConstructorMapper(TodoItem)),
            update_mapper=PydanticDictMapper(UpdateTodoPayload, exclude_unset=True),
            replace_mapper=PydanticDictMapper(AddTodoPayload),
        )
