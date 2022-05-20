from typing import Dict, List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Response, status

from .schemas import TodoItem, TodoItemPayload, UpdateTodoItemPayload


def get_app():  # noqa
    def raise_code(status_code: Optional[int] = None):
        if status_code is not None:
            raise HTTPException(status_code)

    app = FastAPI(
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        dependencies=[Depends(raise_code)],
    )
    data: Dict[UUID, TodoItem] = {}

    @app.get("/", response_model=List[TodoItem])
    def get_items():
        return list(data.values())

    @app.post("/", response_model=TodoItem, status_code=status.HTTP_201_CREATED)
    def add_item(payload: TodoItemPayload):
        new_item = TodoItem(**payload.dict())
        data[new_item.id] = new_item
        return new_item

    def item(id: UUID):
        try:
            item = data[id]
        except KeyError:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        else:
            return item

    @app.get("/{id}", response_model=TodoItem)
    def retrieve_item(item: TodoItem = Depends(item)):
        return item

    @app.patch(
        path="/{id}",
        response_model=TodoItem,
    )
    def update_item(payload: UpdateTodoItemPayload, item: TodoItem = Depends(item)):
        new_item = item.copy(update=payload.dict(exclude_unset=True))
        data[new_item.id] = new_item
        return new_item

    @app.delete(
        path="/{id}",
        response_class=Response,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_item(item: TodoItem = Depends(item)):
        del data[item.id]

    @app.delete(
        path="/",
        response_class=Response,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def cleanup():
        data.clear()

    return app
