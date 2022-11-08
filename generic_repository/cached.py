# pylint: disable=import-error
"""
Cache repository implementation.
"""
import asyncio
import json
from typing import Any, Dict, Generic, List, Optional, TypeVar

from typing_extensions import ParamSpec

from .repository import _A, _I, _R, _U, Repository, _Id

_Out = TypeVar("_Out")
_Params = ParamSpec("_Params")
_FuncOut = TypeVar("_FuncOut")


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
        data = self._get_or_cache(
            self.repository.get_list,
            "list",
            offset=offset,
            size=size,
            **query_filters,
            wrapper=asyncio.create_task,
        )

        return await data

    def _get_or_cache(self, method, prefix, *args, wrapper, **kwargs):
        cache_key = self._gen_cache_key(prefix, *args, **kwargs)
        data = self._cache.get(cache_key)
        if data is None:
            data = wrapper(method(*args, **kwargs))
            self._cache[cache_key] = data
        return data

    def _gen_cache_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        body = json.dumps({**kwargs, "__args": args})
        return f"{prefix}:{body}"

    async def get_count(self, **query_filters: Any) -> int:
        return await self._get_or_cache(
            self.repository.get_count,
            "count",
            **query_filters,
            wrapper=asyncio.create_task,
        )

    async def get_by_id(self, item_id: _Id, **kwargs: Any) -> _I:
        return await self._get_or_cache(
            self.repository.get_by_id,
            "get_by_id",
            item_id,
            **kwargs,
            wrapper=asyncio.create_task,
        )

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
