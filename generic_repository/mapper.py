import abc
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    NamedTuple,
    ParamSpec,
    Sequence,
    Type,
    TypeVar,
    Union,
)

_MapperParams = ParamSpec("_MapperParams")
_In = TypeVar("_In")
_Out = TypeVar("_Out")
_New = TypeVar("_New")


class Mapper(Generic[_In, _Out], abc.ABC):
    """A mapper abstract class.

    Example:
    >>> class MultiplyMapper(Mapper):
    ...     def map_item(self, num, **kwargs):
    ...         return num*2
    ...
    >>> mapper=MultiplyMapper()
    >>> mapper(2)
    4
    >>> mapper(5)
    10
    >>> mapper.reverse_map(4)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    NotImplementedError: ...
    """

    def __call__(self, input: _In, **kwds: Any) -> _Out:
        return self.map_item(input, **kwds)

    @abc.abstractmethod
    def map_item(self, item: _In, **kwargs: Any) -> _Out:
        """Maps an item to it's output representation.

        Args:
            item (_In): The item to map.

        Returns:
            _Out: The output representation.
        """

    def reverse_map(self, out: _Out, **kwargs: Any) -> _In:
        """Reverse the mapping process.

        Args:
            out (_Out): The output to reverse map.

        Returns:
            _In: The input representation.
        """
        raise NotImplementedError("Not implemented.")

    def chain(
        self,
        mapper_factory: Union[
            Callable[_MapperParams, "Mapper[_Out, _New]"], Type["Mapper[_Out, _New]"]
        ],
        *mapper_args: _MapperParams.args,
        **mapper_kwargs: _MapperParams.kwargs
    ) -> "Mapper[_In,_New]":
        """Chain another mapper to this.

        >>> mapper=(
        ...     LambdaMapper(lambda x: x*2, lambda x: x/2)
        ...     .chain(LambdaMapper, lambda x: x*2, lambda x: x/2)
        ... )

        >>> mapper(3)
        12
        >>> mapper.reverse_map(12)
        3.0
        >>>
        """
        mapper = mapper_factory(*mapper_args, **mapper_kwargs)
        return DecoratedMapper(self, mapper)


class LambdaMapper(Mapper[_In, _Out]):
    """A lambda-powered mapper.

    >>> mapper=LambdaMapper(lambda x: x*3, lambda x: x/3)

    >>> mapper.map_item(4)
    12
    >>> mapper.reverse_map(15)
    5.0
    >>> mapper2 = LambdaMapper(lambda x: x*3)

    >>> mapper2.reverse_map(3)
    Traceback (most recent call last):
      ...
    NotImplementedError: ...
    """

    def __init__(
        self, func: Callable[[_In], _Out], reverse_func: Callable[[_Out], _In] = None
    ) -> None:
        super().__init__()
        self.func = func
        self.reverse_func = reverse_func

    def map_item(self, item: _In, **kwargs: Any) -> _Out:
        return self.func(item)

    def reverse_map(self, out: _Out, **kwargs: Any) -> _In:
        if self.reverse_func is not None:
            return self.reverse_func(out)
        return super().reverse_map(out)


_Obj = TypeVar("_Obj")


class _Arguments(NamedTuple):
    args: tuple
    kwargs: Dict[str, Any]


class ToFunctionArgsMapper(Mapper[dict[str, Any] | Sequence, _Arguments]):
    """Maps a dict to kwargs part of a function call.

    Example:
    >>> mapper=ToFunctionArgsMapper()

    >>> mapper({'x':3})
    _Arguments(args=(), kwargs={'x': 3})
    >>> mapper([3])
    _Arguments(args=(3,), kwargs={})
    >>> mapper({3})
    _Arguments(args=(3,), kwargs={})
    >>> mapper((3,))
    _Arguments(args=(3,), kwargs={})
    >>> args, kwargs = mapper((3,), x=2)

    >>> kwargs['x']
    2
    >>> mapper('x')
    Traceback (most recent call last):
      ...
    TypeError: ...
    >>>
    """

    def map_item(self, item, **default_kwargs):
        args: list[Any] = []
        kwargs: dict[str, Any] = {}
        kwargs.update(default_kwargs)
        if isinstance(item, dict):
            kwargs.update(item)
        elif isinstance(item, (tuple, list, set)):
            args.extend(item)
        else:
            raise TypeError("Type not supported.")

        return _Arguments(tuple(args), kwargs)


class ConstructorMapper(Mapper[_Arguments, _Obj], Generic[_Obj]):
    """A from-args to object mapper.

    Example:
    >>> from dataclasses import dataclass

    >>> @dataclass()
    ... class Point:
    ...     x: int
    ...     y: int
    ...
    >>> mapper=ConstructorMapper(Point)

    >>> mapper(((4, 5),{}))
    Point(x=4, y=5)
    >>> mapper(((4,),{'y': 5}))
    Point(x=4, y=5)
    >>> mapper(((),{'y': 5,'x':4}))
    Point(x=4, y=5)
    """

    def __init__(self, cls: Type[_Obj]) -> None:
        super().__init__()
        assert isinstance(cls, type)
        self.cls = cls

    def map_item(self, item: _Arguments, **kwargs: Any) -> _Obj:
        args, kw = item
        return self.cls(*args, **kw)  # type: ignore


_Intermediate = TypeVar("_Intermediate")


class DecoratedMapper(Mapper[_In, _Out]):
    def __init__(
        self, first: Mapper[_In, _Intermediate], second: Mapper[_Intermediate, _Out]
    ) -> None:
        super().__init__()
        self.first, self.second = first, second

    def map_item(self, item: _In, **kwargs: Any) -> _Out:
        return self.second.map_item(self.first.map_item(item, **kwargs), **kwargs)

    def reverse_map(self, out: _Out, **kwargs: Any) -> _In:
        return self.first.reverse_map(self.second.reverse_map(out, **kwargs), **kwargs)
