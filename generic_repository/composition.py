"""
Composite repository implementation.

This implements a composite pattern for repositories.
"""
from typing import Any, Generic, List, Optional, TypeVar

from .mapper import Mapper
from .repository import Repository

_MI = TypeVar("_MI")
_MA = TypeVar("_MA")
_MU = TypeVar("_MU")
_MR = TypeVar("_MR")
_MId = TypeVar("_MId")
_A = TypeVar("_A")
_U = TypeVar("_U")
_R = TypeVar("_R")
_I = TypeVar("_I")
_Id = TypeVar("_Id")


class MappedRepository(
    Repository[_MId, _MA, _MU, _MR, _MI],
    Generic[
        _MId,
        _MA,
        _MU,
        _MR,
        _MI,
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
        id_mapper: Mapper[_MId, _Id],
        create_mapper: Mapper[_MA, _A],
        update_mapper: Mapper[_MU, _U],
        replace_mapper: Mapper[_MR, _R],
        item_mapper: Mapper[_I, _MI],
    ) -> None:
        """Initialize the `MappedRepository` instance.

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

    async def add(self, payload: _MA, **kwargs: Any) -> _MI:
        """Add a new item.

        Args:
            payload (_MA): The payload to use

        Returns:
            _MI: The newly created item
        """
        return await self.map_item(
            await self.repository.add(self.create_mapper(payload), **kwargs)
        )

    async def update(self, item_id: _MId, payload: _MU, **kwargs: Any) -> _MI:
        """Update an item.

        Args:
            item_id (_MId): The item ID to change
            payload (_MU): The data to update with

        Returns:
            _MI: The updated item
        """
        return await self.map_item(
            await self.repository.update(
                self.id_mapper(item_id), self.update_mapper(payload), **kwargs
            )
        )

    async def get_by_id(self, item_id: _MId, **kwargs: Any) -> _MI:
        """Retrieve an item by it's ID.

        Args:
            item_id (_MId): The ID of the item to retrieve

        Returns:
            _MI: The item
        """
        return await self.map_item(
            await self.repository.get_by_id(self.id_mapper(item_id), **kwargs)
        )

    async def replace(self, item_id: _MId, payload: _MR, **kwargs: Any) -> _MI:
        """Replace an item in the underlying store.

        Args:
            item_id (_MId): The item ID to replace
            payload (_MR): The data to replace with

        Returns:
            _MI: The new item
        """
        return await self.map_item(
            await self.repository.replace(
                self.id_mapper(item_id), self.replace_mapper(payload), **kwargs
            )
        )

    async def get_count(self, **query_filters: Any) -> int:
        """Retrieve a count of items.

        Returns:
            int: The item count
        """
        return await self.repository.get_count(**query_filters)

    async def get_list(
        self,
        *,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        **query_filters: Any,
    ) -> List[_MI]:
        """Retrieve a list of items from the undeerlying repository.

        Args:
            offset (Optional[int], optional): The list offset. Defaults to None.
            size (Optional[int], optional): The list size. Defaults to None.

        Returns:
            List[_MI]: A list of items
        """
        return await self.map_item_list(
            await self.repository.get_list(
                offset=offset,
                size=size,
                **query_filters,
            )
        )

    async def remove(self, item_id: _MId, **kwargs: Any):
        """Remove an item from the underlying repository.

        Args:
            item_id (_MId): The item ID to be removed.
        """
        await self.repository.remove(self.id_mapper(item_id), **kwargs)

    async def map_item(self, item: _I) -> _MI:
        """Transform an item.

        Args:
            item (_I): The original item

        Returns:
            _MI: The transformed item
        """
        return self.item_mapper(item)

    async def map_item_list(self, item_list: List[_I]) -> List[_MI]:
        """Map an item list to the correct representation.

        Args:
            item_list (List[_I]): The original item list

        Returns:
            List[_MI]: The mapped item list
        """
        return [self.item_mapper(item) for item in item_list]
