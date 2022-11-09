# pylint: disable=import-error,redefined-outer-name,unused-argument,missing-function-docstring,import-outside-toplevel # noqa E501
# type: ignore
"""
Fixtures for the library.

This module contains fixtures for the test suite.
"""
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from generic_repository import CacheRepository, HttpRepository, MappedRepository
from generic_repository.mapper import LambdaMapper
from generic_repository.pydantic import PydanticDictMapper
from tests.todos import AddTodoPayload, Todo, TodoRepository, UpdateTodoPayload


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def init_database():
    from .sqlalchemy.models import Base  # pylint: disable=import-outside-toplevel

    return Base.metadata.create_all


@pytest.fixture(scope="session")
async def db_engine(init_database, anyio_backend):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.connect() as conn:
        await conn.run_sync(init_database)

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def db_sessionmaker(db_engine: AsyncEngine):
    return sessionmaker(
        bind=db_engine,
        class_=AsyncSession,  # type: ignore
    )


@pytest.fixture(scope="session")
async def db_session(
    db_sessionmaker: "sessionmaker[AsyncSession]", anyio_backend  # type: ignore
):
    session = db_sessionmaker()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture()
async def sa_cleanup(db_session: AsyncSession, anyio_backend):
    from .sqlalchemy.models import TodoItem  # pylint: disable=import-outside-toplevel

    try:
        yield
    finally:
        await db_session.execute(delete(TodoItem))
        await db_session.commit()


@pytest.fixture()
def sa_repository(db_session: AsyncSession, sa_cleanup):
    from .sqlalchemy.todos import DbTodoRepository

    return DbTodoRepository(db_session)


@pytest.fixture()
def mapped_sa_repository(db_session: AsyncSession, sa_cleanup):
    from .sqlalchemy.todos import DbMappedTodoRepository

    return DbMappedTodoRepository(db_session)


@pytest.fixture(scope="session")
def app():
    from .http.app import get_app

    return get_app()


@pytest.fixture()
async def client(app: FastAPI, anyio_backend):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture()
async def cleanup_items(client: AsyncClient, anyio_backend):
    try:
        yield
    finally:
        await client.delete("/")


@pytest.fixture()
def http_repository(client: AsyncClient):
    return HttpRepository(client)


@pytest.fixture()
def http_todos_repository(http_repository: HttpRepository, cleanup_items):
    return MappedRepository(
        http_repository,
        create_mapper=PydanticDictMapper(AddTodoPayload),
        item_mapper=LambdaMapper(Todo.parse_obj),
        update_mapper=PydanticDictMapper(UpdateTodoPayload),
        replace_mapper=PydanticDictMapper(AddTodoPayload),
        id_mapper=LambdaMapper(str, int),
    )


@pytest.fixture()
def cached_repository(http_todos_repository: TodoRepository):
    return CacheRepository(http_todos_repository)


@pytest.fixture(
    params=(
        "sa_repository",
        "http_todos_repository",
        "cached_repository",
        "mapped_sa_repository",
    )
)
def repository(request):
    return request.getfixturevalue(request.param)
