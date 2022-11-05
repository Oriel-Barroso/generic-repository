import asyncio
from functools import wraps

try:  # pragma nocover
    from functools import cache  # type: ignore
except ImportError:  # pragma nocover
    from functools import lru_cache

    cache = lru_cache()
from typing import (
    Any,
    Callable,
    Coroutine,
    Generator,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec

from .base import _A, _I, _R, _U, Repository, _Id

_Params = ParamSpec("_Params")
_FuncOut = TypeVar("_FuncOut")


def _task(
    func: Callable[
        _Params, Union[Generator[Any, None, _FuncOut], Coroutine[Any, Any, _FuncOut]]
    ]
):
    @wraps(func)
    def decorated(
        *args: _Params.args, **kwargs: _Params.kwargs
    ) -> "asyncio.Task[_FuncOut]":
        return asyncio.create_task(func(*args, **kwargs))

    return decorated


class CacheRepository(
    Repository[_Id, _A, _U, _R, _I],
    Generic[_Id, _A, _U, _R, _I],
):
    """A cached repository implementation.

    This implements caching for an underlying repository, provided in the constructor.

    For simplisity, the implementation relies in the functool's caching functionality.

    Note that modify operations are not cached and clear the caches.
    """

    def __init__(self, repository: Repository[_Id, _A, _U, _R, _I]) -> None:
        super().__init__()
        self.repository = repository

    def clear_cache(self):
        self.get_list.cache_clear()
        self.get_count.cache_clear()
        self.get_by_id.cache_clear()

    async def add(self, payload: _A, **kwargs: Any) -> _I:
        return await self.repository.add(payload)

    @cache
    @_task
    async def get_list(
        self,
        *,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        **query_filters: Any
    ) -> List[_I]:
        return await self.repository.get_list(offset=offset, size=size, **query_filters)

    @cache
    @_task
    async def get_count(self, **query_filters: Any) -> int:
        return await self.repository.get_count()

    @cache
    @_task
    async def get_by_id(self, id: _Id) -> _I:
        return await self.repository.get_by_id(id)

    async def update(self, id: _Id, payload: _U, **kwargs: Any) -> _I:
        result = await self.repository.update(id, payload, **kwargs)
        self.clear_cache()
        return result

    async def replace(self, id: _Id, payload: _R, **kwargs: Any) -> _I:
        result = await self.repository.replace(id, payload, **kwargs)
        self.clear_cache()
        await self.get_by_id(id)
        return result

    async def remove(self, id: _Id, **kwargs: Any):
        await self.repository.remove(id, **kwargs)
        self.clear_cache()
