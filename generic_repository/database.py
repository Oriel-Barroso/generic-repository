# pylint: disable=import-error
"""
Database repository pattern.

This module contains a sqlalchemy-powered database implementation.
"""
import abc
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
)

from sqlalchemy import Column, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.sql.selectable import Select

from .exceptions import ItemNotFoundException
from .mapper import Mapper
from .repository import _A, _I, _R, _U, Repository, _Id

_Model = TypeVar("_Model")


class DatabaseRepository(
    Generic[_Model, _A, _U, _R, _I, _Id],
    Repository[_Id, _A, _U, _R, _I],
    abc.ABC,
):
    """Base SQLAlchemy-based cruds.

    Args:
        session (AsyncSession): The session to be used for queries.

    Variables:
        model_class (ClassVar[Type[Base]]): The mapper model class.
        primary_key (sa.Column): The primary key column.
    """

    model_class: ClassVar[Optional[Type[Any]]] = None
    primary_key_column: ClassVar[Optional[Column]] = None

    def __init__(
        self,
        session: AsyncSession,
        item_mapper: Mapper[_Model, _I],
        create_mapper: Mapper[_A, _Model],
        update_mapper: Mapper[_U, Dict[str, Any]],
        replace_mapper: Mapper[_R, Dict[str, Any]],
    ) -> None:
        """Initialize this crud instance.

        Args:
            session (AsyncSession): The SQLAlchemy async session to use.
            item_mapper (Mapper[_Model, _Item]): The mapper implementation to map
                models to items.
            create_mapper (Mapper[_Create, _Model]): Mapper to build item models.
            update_mapper (Mapper[_Update, Dict[str,Any]]): Mapper between update
                payload and dict.
            replace_mapper (Mapper[_Replace, Dict[str,Any]]): Mapper to replace an
                existing item.
        """

        if session is None:
            raise ValueError("Session was not provided.")
        elif not isinstance(session, AsyncSession):  # pragma nocover
            raise TypeError("Invalid session: not an `AsyncSession` instance.")
        self.session = session
        self.item_mapper = item_mapper
        self.create_mapper = create_mapper
        self.update_mapper = update_mapper
        self.replace_mapper = replace_mapper

    @classmethod
    def get_db_model(cls) -> Type[_Model]:  # pragma nocover
        """Retrieve the database model.

        Returns:
            ModelType: The model class to use.
        """
        message: Optional[str] = None
        if cls.model_class is None:
            message = (
                "The database model was not set for `{class_name}`. Please set the "
                "`{class_name}.model_class` attribute or override "
                "`{class_name}.{get_model_method}` method."
            )
        if not isinstance(cls.model_class, DeclarativeMeta):
            message = "The class '{class_name}' is not a SQLALchemy model."
        if message is not None:
            raise AssertionError(
                message.format(
                    get_model_method=cls.get_db_model.__name__,
                    class_name=f"{cls.__module__}.{cls.__qualname__}",  # type: ignore
                )
            )
        return cast(Type[_Model], cls.model_class)

    def get_base_query(self) -> Select:
        """Retrieve a base query.

        Returns:
            Select: The base query.
        """
        return select(self.get_db_model())

    @classmethod
    def get_id_field(cls) -> Column:  # pragma nocover
        """Retrieve the primary key column.

        Multi-column primary keys are not supported.

        Returns:
            sa.Column: The primery key column.
        """
        if cls.primary_key_column is None:
            msg = (
                "The primary key column was not set. Please set the "
                "`{class_name}.primary_key_column` attribute or override the "
                "`{class_name}.{method_name}` method."
            ).format(
                class_name=f"{cls.__module__}.{cls.__name__}",  # type: ignore
                method_name=cls.get_id_field.__name__,
            )
            raise AssertionError(msg)
        return cls.primary_key_column

    def decorate_query(self, query: Select, **query_filters: Any) -> Select:
        # pylint: disable=unused-argument
        """Decorate the given query.

        Adds conditions, ordering and some other query stuff to the given query.

        Parameters:
            select: A base selectable object.

        Returns:
            Select: A modified query.
        """
        return query

    async def get_unmapped_by_id(self, item_id: _Id, **kwargs: Any) -> _Model:
        """Retrieve a raw item from the database.

        Args:
            item_id: The ID of the item to be retrieved.

        Returns:
            The item stored in the database.

        Raises:
            ItemNotFoundException: If the item does not exist.
        """
        result = await self.session.scalar(
            self.decorate_query(self.get_base_query(), **kwargs).where(
                self.get_id_field() == item_id
            )
        )

        if result is None:
            raise ItemNotFoundException()

        return result

    def get_count_query(self, **query_filters: Any) -> Select:
        """Builds a query for counting."""
        return self.decorate_query(
            query=select(
                func.count(),
            ).select_from(self.get_db_model()),
            **query_filters,
        )

    def get_list_query(
        self,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        **query_filters: Any,
    ) -> Select:
        """Builds a query for listing.

        Args:
            offset: The cursor where start retrieving from.
            size: The size of the list to be retrieved.


        Return:
            Select: The resulting query.
        """
        query = self.decorate_query(self.get_base_query(), **query_filters)

        if size:
            query = query.limit(size)

        if offset:
            query = query.offset(offset)

        return query

    def _map_item(self, _session: Session, item: _Model) -> _I:
        return self.item_mapper.map_item(item)

    def _map_items(self, _session: Session, items: Iterable[_Model]) -> List[_I]:
        return [self._map_item(_session, item) for item in items]

    async def get_by_id(self, item_id: _Id, **kwargs: Any) -> _I:
        return await self.session.run_sync(
            self._map_item, await self.get_unmapped_by_id(item_id, **kwargs)
        )

    async def get_count(self, **query_filters: Any) -> int:
        return await self.session.scalar(
            self.get_count_query(**query_filters),
        )

    async def get_list(
        self,
        *,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        **query_filters: Any,
    ) -> List[_I]:
        query = self.get_list_query(offset, size, **query_filters)

        return await self.session.run_sync(
            self._map_items, await self.session.scalars(query)
        )

    async def add(self, payload: _A, **kwargs: Any) -> _I:
        # pylint: disable=isinstance-second-argument-not-valid-type
        model = self.create_mapper(payload)
        if not isinstance(model, self.get_db_model()):  # pragma: nocover
            raise AssertionError(
                "The creation mapper did not built a valid model instance."
            )

        async with self.session.begin_nested():
            await self.postprocess_model(model, **kwargs)
            self.session.add(model)

        return await self.session.run_sync(self._map_item, model)

    async def postprocess_model(self, model: _Model, **extra_values: Any):
        """Does postprocessing of the newly created item.

        Args:
            model: The newly created item.
        """
        for attr, value in extra_values.items():  # pragma nocover
            setattr(model, attr, value)

    async def remove(self, item_id: _Id, **kwargs: Any):
        model = await self.get_unmapped_by_id(item_id, **kwargs)

        async with self.session.begin_nested():
            await self.session.delete(model)

    async def _update(self, item_id: _Id, payload: Dict[str, Any], **kwargs: Any) -> _I:
        model = await self.get_unmapped_by_id(item_id, **kwargs)

        async with self.session.begin_nested():
            self._patch_with(model, payload)

        return await self.session.run_sync(self._map_item, model)

    def _patch_with(self, model: _Model, payload: Dict[str, Any]):
        for attr, value in payload.items():
            setattr(model, attr, value)

    async def update(self, item_id: _Id, payload: _U, **kwargs: Any) -> _I:
        return await self._update(
            item_id, self.update_mapper(payload, exclude_unset=True), **kwargs
        )

    async def replace(self, item_id: _Id, payload: _R, **kwargs: Any):
        return await self._update(item_id, self.replace_mapper(payload), **kwargs)
