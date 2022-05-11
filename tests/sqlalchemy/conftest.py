import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .repository import TodoRepository


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def init_database():
    from .models import Base

    return Base.metadata.create_all


@pytest.fixture(scope="session")
async def db_engine(init_database, anyio_backend):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.connect() as conn:
        await conn.run_sync(init_database)
        await conn.commit()

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def db_sessionmaker(db_engine: AsyncEngine):
    return sessionmaker(db_engine, AsyncSession, autoflush=False)


@pytest.fixture()
async def db_session(db_sessionmaker: "sessionmaker[AsyncSession]", anyio_backend):
    async with db_sessionmaker.begin() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture()
def repository(db_session: AsyncSession):
    return TodoRepository(db_session)
