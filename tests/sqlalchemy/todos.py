# pylint: disable=import-error
"""
Todos database implementation.

Contains some database-powered repository implementations.
"""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from generic_repository import (
    DatabaseRepository,
    LambdaMapper,
    PydanticDictMapper,
    PydanticObjectMapper,
    SqlalchemyMappedRepository,
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
        """Initialize a new todo repository.

        Args:
            session (AsyncSession): The session to use
        """
        super().__init__(
            session=session,
            item_mapper=PydanticObjectMapper(Todo),
            create_mapper=PydanticDictMapper(AddTodoPayload).chain_lambda(
                lambda data: TodoItem(**data)
            ),
            update_mapper=PydanticDictMapper(UpdateTodoPayload, exclude_unset=True),
            replace_mapper=PydanticDictMapper(AddTodoPayload),
        )


class DbMappedTodoRepository(
    SqlalchemyMappedRepository[
        int, AddTodoPayload, UpdateTodoPayload, AddTodoPayload, Todo, TodoItem
    ],
    TodoRepository,
):
    """The todo item database repository."""

    model_class = TodoItem

    def __init__(self, session: AsyncSession) -> None:
        """Initialize a new todo mapped repository.

        Args:
            session (AsyncSession): The session to be used
        """
        super().__init__(
            session=session,
            id_mapper=LambdaMapper[int, Any](lambda x: x),
            item_mapper=PydanticObjectMapper(Todo),
            create_mapper=PydanticDictMapper(AddTodoPayload),
            update_mapper=PydanticDictMapper(UpdateTodoPayload, exclude_unset=True),
            replace_mapper=PydanticDictMapper(AddTodoPayload),
        )
