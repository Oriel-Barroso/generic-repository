from typing import Optional

import pydantic

from generic_repository import Repository


class BaseTodo(pydantic.BaseModel):
    text: Optional[str] = None


class AddTodoPayload(BaseTodo):
    title: str


class UpdateTodoPayload(BaseTodo):
    title: Optional[str] = None


class Todo(AddTodoPayload):
    id: int

    class Config:
        orm_mode = True


class TodoRepository(
    Repository[int, AddTodoPayload, UpdateTodoPayload, AddTodoPayload, Todo]
):
    pass
