import json
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Response, status

from ..todos import AddTodoPayload, Todo, UpdateTodoPayload


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
    data: Dict[int, Dict[str, Any]] = {}

    @app.get("/", response_model=List[Todo])
    def get_items(size: Optional[int] = None, offset: Optional[int] = None):
        items = list(data.values())
        if offset:
            items = items[offset:]
        if size:
            items = items[:size]

        return items

    @app.post("/", response_model=Todo, status_code=status.HTTP_201_CREATED)
    def add_item(
        payload: AddTodoPayload,
        extra_1: Optional[int] = None,
        extra_2: Optional[str] = None,
    ):
        new_item = Todo(**payload.dict(), id=max(data.keys()) + 1 if data else 1)
        data[new_item.id] = json.loads(new_item.json())
        return new_item

    def item(id: int):
        try:
            item = data[id]
        except KeyError:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        else:
            return Todo.parse_obj(item)

    @app.get("/{id}", response_model=Todo)
    def retrieve_item(item: Todo = Depends(item)):
        return item

    @app.patch(
        path="/{id}",
        response_model=Todo,
    )
    def update_item(payload: UpdateTodoPayload, item: Todo = Depends(item)):
        new_item = item.copy(update=payload.dict(exclude_unset=True))
        data[new_item.id] = json.loads(new_item.json())
        return new_item

    @app.delete(
        path="/{id}",
        response_class=Response,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_item(item: Todo = Depends(item)):
        del data[item.id]

    @app.delete(
        path="/",
        response_class=Response,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def cleanup():
        data.clear()

    @app.put("/{id}", response_model=Todo)
    def replace_item(payload: AddTodoPayload, item: Todo = Depends(item)):
        new_item = dict(**json.loads(payload.json()), id=item.id)
        data[item.id] = new_item
        return Todo.parse_obj(new_item)

    return app
