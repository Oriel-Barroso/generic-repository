"""
Composite repository implementation.
"""
from typing import Any, Generic, List, Optional, TypeVar

from .mapper import Mapper
from .repository import _A, _I, _R, _U, Repository, _Id

_Repo = TypeVar("_Repo", bound=Repository)
_MappedItem = TypeVar("_MappedItem")
_MappedCreate = TypeVar("_MappedCreate")
_MappedUpdate = TypeVar("_MappedUpdate")
_MappedReplace = TypeVar("_MappedReplace")
_MappedId = TypeVar("_MappedId")


class MappedRepository(
    Repository[_MappedId, _MappedCreate, _MappedUpdate, _MappedReplace, _MappedItem],
    Generic[
        _MappedId,
        _MappedCreate,
        _MappedUpdate,
        _MappedReplace,
        _MappedItem,
        _Id,
        _A,
        _U,
        _R,
        _I,
    ],
):
    """Mapped data for repositories.

    This implements the repository interface by leveraging mappers between payloads,
    item and id for an underlying repository implementation.
    """

    def __init__(
        self,
        repository: Repository[_Id, _A, _U, _R, _I],
        *,
        id_mapper: Mapper[_MappedId, _Id],
        create_mapper: Mapper[_MappedCreate, _A],
        update_mapper: Mapper[_MappedUpdate, _U],
        replace_mapper: Mapper[_MappedReplace, _R],
        item_mapper: Mapper[_I, _MappedItem],
    ) -> None:
        """
        Initialize the `MappedRepository` instance.

        Args:
            id_mapper: A mapper to transform the item ID.
            create_mapper: A mapper to add new items.
            update_mapper: Mapper to update an item.
            replace_mapper: Maps the replace payload.
            item_mapper: The item mapper from the repository implementation.
            repository: The underlying repository implementations.
        """
        super().__init__()
        self.repository = repository
        self.item_mapper = item_mapper
        self.id_mapper = id_mapper
        self.create_mapper = create_mapper
        self.update_mapper = update_mapper
        self.replace_mapper = replace_mapper

    async def add(self, payload: _MappedCreate, **kwargs: Any) -> _MappedItem:
        return self.item_mapper(
            await self.repository.add(self.create_mapper(payload), **kwargs)
        )

    async def update(
        self, item_id: _MappedId, payload: _MappedUpdate, **kwargs: Any
    ) -> _MappedItem:
        return self.item_mapper(
            await self.repository.update(
                self.id_mapper(item_id), self.update_mapper(payload), **kwargs
            )
        )

    async def get_by_id(self, item_id: _MappedId, **kwargs: Any) -> _MappedItem:
        return self.item_mapper(
            await self.repository.get_by_id(self.id_mapper(item_id), **kwargs)
        )

    async def replace(
        self, item_id: _MappedId, payload: _MappedReplace, **kwargs: Any
    ) -> _MappedItem:
        return self.item_mapper(
            await self.repository.replace(
                self.id_mapper(item_id), self.replace_mapper(payload), **kwargs
            )
        )

    async def get_count(self, **query_filters: Any) -> int:
        return await self.repository.get_count(**query_filters)

    async def get_list(
        self,
        *,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        **query_filters: Any,
    ) -> List[_MappedItem]:
        return [
            self.item_mapper(item)
            for item in await self.repository.get_list(
                offset=offset, size=size, **query_filters
            )
        ]

    async def remove(self, item_id: _MappedId, **kwargs: Any):
        return await self.repository.remove(self.id_mapper(item_id), **kwargs)
