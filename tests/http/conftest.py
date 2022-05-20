import httpx
import pytest

from generic_repository import HttpRepository

from .app import get_app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app():
    return get_app()


@pytest.fixture(scope="session")
async def client(app, anyio_backend):
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
async def cleanup_items(client: httpx.AsyncClient, anyio_backend):
    try:
        yield
    finally:
        await client.delete("/")


@pytest.fixture()
def repo(client: httpx.AsyncClient):
    return HttpRepository(client)
