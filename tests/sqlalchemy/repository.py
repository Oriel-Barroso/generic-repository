import pydantic
from sqlalchemy.ext.asyncio import AsyncSession

from generic_repository.database import DatabaseRepository
from generic_repository.mapper import ConstructorMapper, ToFunctionArgsMapper
from generic_repository.pydantic import PydanticDictMapper, PydanticObjectMapper

from .models import TodoItem


class BaseTodo(pydantic.BaseModel):
    text: str | None = None


class AddTodoPayload(BaseTodo):
    title: str


class UpdateTodoPayload(BaseTodo):
    title: str | None = None


class Todo(AddTodoPayload):
    id: int

    class Config:
        orm_mode = True


class TodoRepository(
    DatabaseRepository[TodoItem, AddTodoPayload, UpdateTodoPayload, Todo, int]
):
    model_class = TodoItem
    primary_key_column = TodoItem.id

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session,
            PydanticObjectMapper(Todo),
            PydanticDictMapper(AddTodoPayload)
            .chain(ToFunctionArgsMapper)  # type: ignore
            .chain(ConstructorMapper, TodoItem),  # type: ignore
            PydanticDictMapper(AddTodoPayload, UpdateTodoPayload),
        )
