from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TodoItemPayload(BaseModel):
    body: Optional[str]
    complete: bool = False
    title: str


class TodoItem(TodoItemPayload):
    id: UUID = Field(default_factory=uuid4)


class UpdateTodoItemPayload(BaseModel):
    body: Optional[str]
    complete: bool = False
    title: Optional[str]
