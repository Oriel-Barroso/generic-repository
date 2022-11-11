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
    Protocol,
    Sequence,
    Type,
    TypeVar,
    cast,
)

from sqlalchemy import Column, func, inspect, select  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.sql.selectable import Select

from .composition import MappedRepository
from .exceptions import ItemNotFoundException
from .mapper import Mapper
from .repository import Repository

_Model = TypeVar("_Model")
_A = TypeVar("_A")
_I = TypeVar("_I")
_R = TypeVar("_R")
_U = TypeVar("_U")
_Id = TypeVar("_Id")


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
    primary_key_column: ClassVar[Optional[Column[Any]]] = None

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
    def get_id_field(cls) -> Column[Any]:  # pragma nocover
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
        """Build a query for counting."""
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
        """Build a query for listing.

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
        """Return an item from the database.

        Args:
            item_id (_Id): The item ID

        Returns:
            _I: The item stored in the database, if any.
        """
        return await self.session.run_sync(
            self._map_item, await self.get_unmapped_by_id(item_id, **kwargs)
        )

    async def get_count(self, **query_filters: Any) -> int:
        """Retrieve the number of items in the database.

        Returns:
            int: The item count.
        """
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
        """Retrieve a list of items from the database.

        Args:
            offset (Optional[int], optional): The offset where to start retrieving from.
                Defaults to None.
            size (Optional[int], optional): The size of the list. Defaults to None.

        Returns:
            List[_I]: A list of items
        """
        query = self.get_list_query(offset, size, **query_filters)

        return await self.session.run_sync(
            self._map_items, await self.session.scalars(query)
        )

    async def add(self, payload: _A, **kwargs: Any) -> _I:
        # pylint: disable=isinstance-second-argument-not-valid-type
        """Add an item to the database.

        Args:
            payload (_A): The item payload

        Raises:
            AssertionError: If the produced object is not a valid model

        Returns:
            _I: The newly created item
        """
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
        """Do postprocessing of the newly created item.

        Args:
            model: The newly created item.
        """
        for attr, value in extra_values.items():  # pragma nocover
            setattr(model, attr, value)

    async def remove(self, item_id: _Id, **kwargs: Any):
        """Remove an item from the database.

        Args:
            item_id (_Id): The item ID to be removed
        """
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
        """Update an item in the database.

        Args:
            item_id (_Id): The ID of the item to be changed
            payload (_U): The data to apply to the item

        Returns:
            _I: The new, updated item
        """
        return await self._update(item_id, self.update_mapper(payload), **kwargs)

    async def replace(self, item_id: _Id, payload: _R, **kwargs: Any) -> _I:
        """Replace the entire item in the database.

        Args:
            item_id (_Id): The item ID to be replaced
            payload (_R): The new data of the item

        Returns:
            _I: The new item
        """
        return await self._update(item_id, self.replace_mapper(payload), **kwargs)


class _QueryFilter(Protocol):  # pragma: nocover
    def __call__(self, query: Select, **query_filters: Any) -> Select:
        ...


class SqlalchemyModelRepository(
    Repository[Any, Dict[str, Any], Dict[str, Any], Dict[str, Any], _Model],
    Generic[_Model],
    abc.ABC,
):
    """A sqlalchemy database model repository."""

    model_class: ClassVar[Optional[Type[Any]]] = None
    primary_key: ClassVar[Optional[Any]] = None

    def __init__(
        self,
        session: AsyncSession,
        *,
        filter_query: Optional[_QueryFilter] = None,
        model_class: Optional[Type[_Model]] = None,
        primary_key_column: Optional[Any] = None,
    ) -> None:
        """Initialize a new model repository.

        Args:
            session: The session to use inside this instance
            filter_query: A query filter function

        example:
        >>> from unittest import mock
        >>> mocked_session = mock.Mock()
        >>> mocked_class=mock.Mock()
        >>> mocked_pk=mock.Mock()
        >>> SqlalchemyModelRepository(mocked_session)
        <...>
        >>> SqlalchemyModelRepository(mocked_session, model_class=mocked_class)
        <...>
        >>> SqlalchemyModelRepository(
        ...     mocked_session,
        ...     model_class=mocked_class,
        ...     primary_key_column=mocked_pk
        ... )
        <...>
        >>>
        """
        super().__init__()
        self.session = session
        self.query_filter = filter_query
        if model_class is not None:
            self.model_class = model_class  # type: ignore

        if primary_key_column:
            self.primary_key = primary_key_column  # type: ignore

    def get_db_model(self) -> Type[_Model]:
        """Return the sqlalchemy model class.

        Override this to do things like lazy imports.

        Raising error:
        >>> from unittest import mock
        >>> session=mock.Mock()
        >>> repo = SqlalchemyModelRepository(session)
        >>> repo.get_db_model()
        Traceback (most recent call last):
          ...
        NotImplementedError: ...

        Invalid class:
        >>> class B: pass
        >>> repo = SqlalchemyModelRepository(session, model_class=B)
        >>> repo.get_db_model()
        Traceback (most recent call last):
          ...
        AssertionError: ...
        """
        model_class = self.model_class
        if model_class is None:
            cls_qualname = f"{type(self).__module__}.{type(self).__qualname__}"
            method_name = self.get_db_model.__name__
            raise NotImplementedError(
                f"Class `{cls_qualname}.model_class` attribute is not set. Either set "
                f"the attribute or override the method `{cls_qualname}.{method_name}` "
                "method to fix this."
            )
        if not isinstance(model_class, DeclarativeMeta):
            model_qualname = f"{model_class.__module__}.{model_class.__qualname__}"
            raise AssertionError(f"Class `{model_qualname}` is not a SQLAlchemy model.")

        return cast(Type[_Model], model_class)

    @property
    def primary_key_columns(self):
        """Return the primary key of the model."""
        if self.primary_key is not None:
            return self.primary_key
        inspection = inspect(self.get_db_model())

        pk_columns = inspection.primary_key

        return pk_columns

    def get_items_query(self) -> Select:
        """Return the base query to act on.

        The returned value must be a SQLAlchemy
        `sqlalchemy.select` construct. You can chain calls to
        any method of this class.
        """
        return select(self.get_db_model())

    def _match_id(self, query: Select, item_id: Any) -> Select:
        primary_key = self.primary_key_columns
        values: tuple[Any, ...] = ()
        if len(primary_key) == 0:
            raise AssertionError("Invalid primary key: No columns specified.")
        if isinstance(item_id, (list, tuple, set, frozenset)):
            values = tuple(item_id)  # type: ignore
        else:
            values = (item_id,)
        if len(values) != len(primary_key):
            raise AssertionError(
                f"Primary key has {len(primary_key)} columns and the `item_id` is "
                f"{len(values)} length."
            )
        for idx, value in enumerate(values):
            query = query.where(primary_key[idx] == value)

        return query

    def filter_query(  # pylint: disable=unused-argument
        self,
        query: Select,
        *,
        cursor: Any = None,
        **query_filters: Any,
    ) -> Select:
        """Apply filters to the query.

        Args:
            query (Select): The query to be filtered
            cursor (Any, optional): A cursor to apply to the query. Defaults to None.

        Returns:
            Select: A new query with filters applied
        """
        if cursor is not None:
            query = self.apply_cursor(query, cursor)

        if self.query_filter is not None:
            query = self.query_filter(query, **query_filters)

        return query

    def apply_cursor(self, query: Select, cursor: Any) -> Select:
        """Apply the cursor to a query.

        Args:
            query (Select): The query to apply to
            cursor (Any): The cursor value to be applied

        Raises:
            NotImplementedError: If the class does not cursor pagination

        Returns:
            Select: The query with the cursor filter applied
        """
        raise NotImplementedError()

    def get_list_query(
        self,
        *,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        **query_filters: Any,
    ) -> Select:
        """Return a query for item list.

        Args:
            offset (Optional[int], optional): How many items to skip before starting to.
                Defaults to None.
            size (Optional[int], optional): The size of the query. Defaults to None.

        Returns:
            Select: The query to be executed.
        """
        query = self.filter_query(
            self.get_items_query(),
            **query_filters,
        )
        if offset is not None:
            query = query.offset(offset=offset)

        if size is not None:
            query = query.limit(limit=size)

        return query

    def get_count_query(self) -> Select:
        """Build a query for counting.

        Returns:
            Select: The base query built from the model
        """
        return select(func.count()).select_from(self.get_db_model())

    async def get_count(self, **query_filters: Any) -> int:
        """Count all model instances saved in the database.

        Returns:
            int: The number of items in the database
        """
        query = self.filter_query(
            query=self.get_count_query(),
            **query_filters,
        )
        results = await self.session.scalar(query)

        return results

    async def add(self, payload: Dict[str, Any], **kwargs: Any) -> _Model:
        """Add a new model instance to the database.

        Args:
            payload (Dict[str, Any]): The data to set to the model

        Returns:
            _Model: The newly added instance.
        """
        instance = self._build_model_instance(payload)

        await self.before_save(instance, True)

        async with self.session.begin_nested():
            await self.preprocess_instance(instance, True)
            self.session.add(instance)
            await self.postprocess_instance(instance, True)

        await self.after_save(instance, True)
        return instance

    def _build_model_instance(self, payload: Dict[str, Any]) -> _Model:
        model = self.get_db_model()
        instance = model()  # pylint: disable=not-callable
        for key, value in payload.items():
            setattr(instance, key, value)
        return instance

    def get_item_query(self, item_id: Any, **query_filters: Any) -> Select:
        """Retrieve the query to obtain a single item.

        Args:
            item_id (Any): The item ID to be retrieved

        Returns:
            Select: The single item query
        """
        query = self._match_id(
            query=self.filter_query(
                query=self.get_items_query(),
                **query_filters,
            ),
            item_id=item_id,
        ).limit(1)

        return query

    async def get_by_id(self, item_id: Any, **query_filters: Any) -> _Model:
        """Retrieve a single item from the database.

        Args:
            item_id (Any): The ID to retrieve

        Raises:
            ItemNotFoundException: If the item does not exist in the database

        Returns:
            _Model: The item stored in the database
        """
        query = self.get_item_query(item_id, **query_filters)
        instance = await self.session.scalar(query)

        if instance is None:
            raise ItemNotFoundException("Instance not found in database.")

        return instance

    async def get_list(
        self,
        *,
        offset: Optional[int] = None,
        size: Optional[int] = None,
        cursor: Optional[Any] = None,
        **query_filters: Any,
    ) -> List[_Model]:
        """Retrieve a list of items stored in the database.

        Args:
            offset (Optional[int], optional): The database offset. Defaults to None.
            size (Optional[int], optional): The size of the query. Defaults to None.
            cursor (Optional[Any], optional): The cursor. Defaults to None.

        Returns:
            List[_Model]: The list of items in the database
        """
        query = self.get_list_query(
            offset=offset,
            size=size,
            cursor=cursor,
            **query_filters,
        )
        results = await self.session.scalars(query)
        return results.all()

    async def update(
        self, item_id: Any, payload: Dict[str, Any], **query_filters: Any
    ) -> _Model:
        """Update an item in the database.

        Args:
            item_id (Any): The ID of the item to change
            payload (Dict[str, Any]): The data to be applied

        Returns:
            _Model: The updated item
        """
        instance = await self.get_by_id(item_id, **query_filters)

        await self.before_update(instance)
        await self.before_save(instance, False)

        async with self.session.begin_nested():
            await self.preprocess_instance(instance, False)
            await self.perform_update(instance, payload)

            await self.postprocess_instance(instance, False)

        await self.after_save(instance, False)
        await self.before_update(instance)
        return instance

    async def perform_update(self, instance: _Model, payload: Dict[str, Any]):
        """Perform an update.

        Args:
            instance (_Model): The instance to act on
            payload (Dict[str, Any]): The payload to apply
        """
        for key, value in payload.items():
            setattr(instance, key, value)

    async def replace(  # pylint: disable=unused-argument
        self,
        item_id: Any,
        payload: Dict[str, Any],
        **query_filters: Any,
    ) -> _Model:
        """Replace an item in the database.

        Args:
            item_id (Any): The item ID to replace
            payload (Dict[str, Any]): The data to replace the item with

        Returns:
            _Model: The new instance
        """
        old_instance = await self.get_by_id(item_id, **query_filters)
        instance = self._build_model_instance(payload)
        self._add_primary_keys(item_id, instance)

        await self.before_save(old_instance, True)
        await self.before_replace(old_instance)

        async with self.session.begin_nested():
            await self.preprocess_instance(instance, False)
            await self.session.merge(instance)
            await self.postprocess_instance(instance, False)

        await self.after_replace(instance)
        await self.after_save(instance, True)
        return instance

    def _add_primary_keys(self, item_id: Any, instance: _Model):
        id_values: Sequence[Any] = ()
        if isinstance(item_id, (list, tuple, set)):
            id_values = tuple(id_values)
        else:
            id_values = (item_id,)
        inspected = inspect(self.get_db_model())
        for idx, col in enumerate(self.primary_key_columns):
            prop = inspected.get_property_by_column(col)  # type: ignore
            setattr(instance, prop.key, id_values[idx])  # type: ignore

    async def before_save(self, instance: _Model, created: bool):
        """Perform an action before the object save process.

        Args:
            instance (_Model): The instance to be processed
            created (bool): Indicates wether the instance is a new object
        """

    async def after_save(self, instance: _Model, created: bool):
        """Perform actions after the object has been saved.

        Args:
            instance (_Model): The instance object
            created (bool): Indicate if the object is new
        """

    async def preprocess_instance(self, instance: _Model, created: bool):
        """Do something before the is added to the session.

        Args:
            instance (_Model): The instance to be processed
            created (bool): Indicates if the instance is new
        """

    async def postprocess_instance(self, instance: _Model, created: bool):
        """Do a postprocess step.

        Args:
            instance (_Model): The instance to be processed
            created (bool): Indicates if the instance is a new object
        """

    async def before_update(self, instance: _Model):
        """Do something before an update.

        Args:
            instance (_Model): The instance to apply the update to
        """

    async def after_update(self, instance: _Model):
        """Do something after an object has been updated.

        Args:
            instance (_Model): The instance to act on
        """

    async def before_replace(self, instance: _Model):
        """Do something before an object is replaced.

        Args:
            instance (_Model): The object to replace.
        """

    async def after_replace(self, instance: _Model):
        """Do something after the replace has been finished.

        Args:
            instance (_Model): The replaced object instance
        """

    async def remove(self, item_id: Any, **kwargs: Any):
        """Remove an item from the database.

        Args:
            item_id (Any): The item ID to be removed
        """
        instance = await self.get_by_id(item_id, **kwargs)
        await self.before_remove(instance)
        async with self.session.begin_nested():
            await self.perform_remove(instance)

        await self.after_remove(instance)

    async def perform_remove(self, instance: _Model):
        """Remove an item.

        This method performs the real deletion.

        Override this to implement soft deletion.

        Args:
            instance (_Model): The instance to be removed
        """
        await self.session.delete(instance)

    async def before_remove(self, instance: _Model):
        """Do something before the object is removed.

        Args:
            instance (_Model): The instance to act on
        """

    async def after_remove(self, instance: _Model):
        """Do something after the instance has been removed.

        Args:
            instance (_Model): The object instance to act on
        """


class SqlalchemyMappedRepository(
    MappedRepository[
        _Id,
        _A,
        _U,
        _R,
        _I,
        Any,
        Dict[str, Any],
        Dict[str, Any],
        Dict[str, Any],
        _Model,
    ],
    Generic[_Id, _A, _U, _R, _I, _Model],
):
    """A SQLAlchemy mapped repository."""

    model_class: ClassVar[Optional[Any]] = None

    def __init__(
        self,
        session: AsyncSession,
        *,
        id_mapper: Mapper[_Id, Any],
        create_mapper: Mapper[_A, Dict[str, Any]],
        update_mapper: Mapper[_U, Dict[str, Any]],
        replace_mapper: Mapper[_R, Dict[str, Any]],
        item_mapper: Mapper[_Model, _I],
    ) -> None:
        """Initialize a new SqlalchemyMappedRepository.

        Args:
            session (AsyncSession): The session to use
            id_mapper (Mapper[_Id, Any]): The item ID mapper
            create_mapper (Mapper[_A, Dict[str, Any]]): The create mapper
            update_mapper (Mapper[_U, Dict[str, Any]]): The update mapper
            replace_mapper (Mapper[_R, Dict[str, Any]]): The replace mapper
            item_mapper (Mapper[_Model, _I]): The item mapper
        """
        super().__init__(
            repository=SqlalchemyModelRepository(
                session=session,
                filter_query=self.decorate_query,
                model_class=type(self).model_class,
            ),
            id_mapper=id_mapper,
            create_mapper=create_mapper,
            update_mapper=update_mapper,
            replace_mapper=replace_mapper,
            item_mapper=item_mapper,
        )
        self.session = session

    def decorate_query(  # pylint: disable=unused-argument
        self,
        query: Select,
        **query_filters: Any,
    ) -> Select:
        """Decorate a query.

        Args:
            query (Select): The query to be decorated

        Returns:
            Select: The new, decorated query
        """
        return query

    async def map_item(self, item: _Model) -> _I:
        return await self.session.run_sync(lambda s, i: self.item_mapper(i), item)

    async def map_item_list(self, item_list: List[_Model]) -> List[_I]:
        return await self.session.run_sync(
            lambda s, l: [self.item_mapper(i) for i in l],
            item_list,
        )
