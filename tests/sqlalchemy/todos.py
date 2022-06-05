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
    model_class = TodoItem
    primary_key_column = TodoItem.id  # type: ignore

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session,
            PydanticObjectMapper(Todo),
            PydanticDictMapper(AddTodoPayload)
            .chain(ToFunctionArgsMapper)  # type: ignore
            .chain(ConstructorMapper, TodoItem),  # type: ignore
            PydanticDictMapper(UpdateTodoPayload),
            PydanticDictMapper(AddTodoPayload),
        )
