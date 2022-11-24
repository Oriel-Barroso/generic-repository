# mypy: ignore-errors
from typing import Optional
from unittest import mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from generic_repository import (
    LambdaMapper,
    PydanticDictMapper,
    PydanticObjectMapper,
    SqlalchemyMappedRepository,
    SqlalchemyModelRepository,
)

from .. import todos
from . import models


class _TodoModelRepository(SqlalchemyModelRepository[models.TodoItem]):
    model_class = models.TodoItem


class _MappedRepoWithoutModel(
    SqlalchemyMappedRepository[
        int,
        todos.AddTodoPayload,
        todos.UpdateTodoPayload,
        todos.AddTodoPayload,
        todos.Todo,
        models.TodoItem,
    ]
):
    pass

    def __init__(
        self,
        *,
        session: Optional[AsyncSession] = None,
        repository: Optional[_TodoModelRepository] = None,
    ) -> None:
        super().__init__(
            session=session,
            repository=repository,
            id_mapper=LambdaMapper(lambda x: x),
            create_mapper=PydanticDictMapper(todos.AddTodoPayload),
            update_mapper=PydanticDictMapper(
                todos.UpdateTodoPayload, exclude_unset=True
            ),
            replace_mapper=PydanticDictMapper(todos.AddTodoPayload),
            item_mapper=PydanticObjectMapper(todos.Todo),
        )


class _MappedRepo(_MappedRepoWithoutModel):
    model_class = models.TodoItem


@pytest.fixture()
def repo(db_session: AsyncSession):
    return _TodoModelRepository(db_session)


def test_call_existing_filter(repo: _TodoModelRepository):
    mocked_filter = mock.Mock()
    repo._filter_group_id = mocked_filter  # type: ignore
    query = repo.get_list_query(group_id=1)

    mocked_filter.assert_called_with(mock.ANY, 1)
    assert query == mocked_filter.return_value


def test_call_nonexisting_filter(repo: _TodoModelRepository):
    repo.get_list_query(group_id=1)


def test_return_set_pk(repo: _TodoModelRepository):
    mocked_pk = object()
    repo.primary_key = mocked_pk  # type: ignore
    assert repo.primary_key_columns is mocked_pk


def test_returns_model_pk(repo: _TodoModelRepository):
    assert repo.primary_key_columns == (models.TodoItem.id,)


def test_match_without_id(repo: _TodoModelRepository):
    repo.primary_key = ()  # type: ignore
    with pytest.raises(AssertionError):
        repo.get_item_query(1)


def test_match_with_unmatching_id_items(repo: _TodoModelRepository):
    with pytest.raises(AssertionError):
        repo.get_item_query((1, 2))


def test_apply_cursor(repo: _TodoModelRepository):
    mocked_apply_cursor = mock.Mock()
    repo.apply_cursor = mocked_apply_cursor
    repo.get_list_query(cursor=5)
    mocked_apply_cursor.assert_called_with(mock.ANY, 5)


def test_mapped_repository_with_repo(repo: _TodoModelRepository):
    other_repo = _MappedRepo(repository=repo)
    assert other_repo.repository is repo


def test_mapped_repository_with_session(db_session: AsyncSession):
    other_repo = _MappedRepo(session=db_session)
    assert other_repo.session is db_session


def test_mapped_repository_without_anything(db_session: AsyncSession):
    with pytest.raises(TypeError):
        _MappedRepo()


def test_without_class_cannot_construct_with_session(db_session: AsyncSession):
    with pytest.raises(RuntimeError):
        _MappedRepoWithoutModel(session=db_session)


def test_without_model_can_construct_with_repo(repo: _TodoModelRepository):
    _MappedRepoWithoutModel(repository=repo)
