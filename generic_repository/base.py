"""
The repository module.

This module contains the base class `Repository`.
"""
import abc
from typing import Any, Generic, List, Optional, TypeVar

_A = TypeVar("_A")
_U = TypeVar("_U")
_R = TypeVar("_R")
_I = TypeVar("_I")
_Id = TypeVar("_Id")


class Repository(Generic[_Id, _A, _U, _R, _I], abc.ABC):  # pragma nocover
    """Base class for all CRUD implementations."""

    @abc.abstractmethod
    async def get_by_id(self, item_id: _Id, **kwargs: Any) -> _I:
        """Retrieve an item by it's ID.

        Args:
            item_id: The item ID to retrieve.

        Returns:
            _Item: The item.

        Raises:
            ItemNotFoundError: If the item cannot be found.
        """
        raise NotImplementedError()

    async def get_count(self, **query_filters: Any) -> int:
        """Retrieve a total count of items.

        Returns:
            int: _description_
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_list(
        self,
        *,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        **query_filters: Any
    ) -> List[_I]:
        """Retrieve a list of items.

        Args:
            offset: Where to start retrieving items.. Defaults to None.
            size: How many items to retrieve.. Defaults to None.

        Returns:
            List[_Item]: A list containing the items found.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def add(self, payload: _A, **kwargs: Any) -> _I:
        """Add a new item.

        Args:
            payload: The data to use when adding the new item.

        Raises:
            InvalidPayloadException: If the payload is not valid.

        Returns:
            _Item: The newly created item.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def remove(self, item_id: _Id, **kwargs: Any):
        """Remove the item identified by the supplied ID.

        Args:
            item_id: The item ID to remove.

        Raises:
            ItemNotFoundException: If the item does not exist.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def update(self, item_id: _Id, payload: _U, **kwargs: Any) -> _I:
        """Update an item.

        Args:
            item_id: The item ID to update.
            payload: The new data to apply to the item.

        Returns:
            _Item: The updated item.

        Raises:
            ItemNotFoundError: If the item cannot be found.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def replace(self, item_id: _Id, payload: _R, **kwargs: Any) -> _I:
        """Replace an item in the store.

        Args:
            item_id: The item ID to update.
            payload: The new data to apply to the item.

        Returns:
            _Item: The updated item.

        Raises:
            ItemNotFoundError: If the item cannot be found.
        """
        raise NotImplementedError()
