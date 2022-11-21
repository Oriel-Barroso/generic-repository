# pylint: disable=import-error
# mypy: ignore-errors
"""
Cache repository implementation.
"""
import asyncio
import json
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from typing_extensions import ParamSpec

from .repository import Repository

_A = TypeVar("_A")
_U = TypeVar("_U")
_R = TypeVar("_R")
_Id = TypeVar("_Id")
_I = TypeVar("_I")
_WRapperIn = TypeVar("_WRapperIn")
_WrapperOut = TypeVar("_WrapperOut")
_Params = ParamSpec("_Params")


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
        self._cache: Dict[str, Any] = {}

    def clear_cache(self):
        """Clears the repository-level cache."""

        self._cache.clear()

    async def add(self, payload: _A, **kwargs: Any) -> _I:
        return await self.repository.add(payload)

    async def get_list(
        self,
        *,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        **query_filters: Any,
    ) -> List[_I]:
        data: asyncio.Task[List[_I]] = self._get_or_cache(
            self.repository.get_list,
            "list",
            asyncio.create_task,
            offset=offset,
            size=size,
            **query_filters,
        )

        return await data

    def _get_or_cache(
        self,
        method: Callable[_Params, _WRapperIn],
        prefix: str,
        wrapper: Callable[[_WRapperIn], _WrapperOut],
        *args: _Params.args,
        **kwargs: _Params.kwargs,
    ) -> _WrapperOut:
        cache_key = self._gen_cache_key(prefix, *args, **kwargs)
        data = self._cache.get(cache_key)
        if data is None:
            original_data = method(*args, **kwargs)
            data = wrapper(original_data)
            self._cache[cache_key] = data
        return data

    def _gen_cache_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        body = json.dumps({**kwargs, "__args": args})
        return f"{prefix}:{body}"

    async def get_count(self, **query_filters: Any) -> int:
        data: asyncio.Task[int] = self._get_or_cache(
            self.repository.get_count,
            "count",
            asyncio.create_task,
            **query_filters,
        )

        return await data

    async def get_by_id(self, item_id: _Id, **kwargs: Any) -> _I:
        data: asyncio.Task[_I] = self._get_or_cache(
            self.repository.get_by_id,
            "get_by_id",
            asyncio.create_task,
            item_id,
            **kwargs,
        )

        return await data

    async def update(self, item_id: _Id, payload: _U, **kwargs: Any) -> _I:
        result = await self.repository.update(item_id, payload, **kwargs)
        self.clear_cache()
        return result

    async def replace(self, item_id: _Id, payload: _R, **kwargs: Any) -> _I:
        result = await self.repository.replace(item_id, payload, **kwargs)
        self.clear_cache()
        await self.get_by_id(item_id)
        return result

    async def remove(self, item_id: _Id, **kwargs: Any):
        await self.repository.remove(item_id, **kwargs)
        self.clear_cache()
