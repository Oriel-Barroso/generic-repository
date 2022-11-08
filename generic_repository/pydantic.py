# pylint: disable=import-error
"""
Pydantic mappers for repositories.
"""
from typing import Any, Dict, Generic, Type, TypeVar

import pydantic

from .mapper import Mapper

_Model = TypeVar("_Model", bound=pydantic.BaseModel)


class PydanticDictMapper(Mapper[_Model, Dict[str, Any]], Generic[_Model]):
    """Pydantic to dict converter.

    Example:
    >>> class A(pydantic.BaseModel):
    ...     x: int
    ...
    >>> class B:
    ...     x: int
    ...     def __init__(self, x: int):
    ...         self.x = x
    ...
    >>> PydanticDictMapper(B)
    Traceback (most recent call last):
      ...
    TypeError: ...
    >>> mapper=PydanticDictMapper(A)

    >>> mapper(A(x=3))
    {'x': 3}
    >>> mapper(B(3))
    Traceback (most recent call last):
      ...
    AssertionError: ...
    >>>
    """

    def __init__(self, *model_classes: Type[_Model], **dict_kwargs: Any) -> None:
        for model in model_classes:
            if not issubclass(model, pydantic.BaseModel):
                class_name = f"{model.__module__}.{model.__qualname__}"
                raise TypeError(f"The class `{class_name}` is not a pydantic model.")

        super().__init__()

        self._model_classes = model_classes
        self._dict_kwargs = dict_kwargs

    def map_item(self, item: _Model) -> Dict[str, Any]:
        if not any(map(lambda x: isinstance(item, x), self._model_classes)):
            raise AssertionError("The passed object isnot of any provided class.")

        return item.dict(**self._dict_kwargs)


class PydanticObjectMapper(Mapper[Any, _Model], Generic[_Model]):
    """Pydantic object mapper.

    This requires the orm mode to be enabled in the models.
    """

    def __init__(self, model_class: Type[_Model]) -> None:
        if not model_class.Config.orm_mode:
            model_class_qualname = (
                f"{model_class.__module__}.{model_class.__qualname__}"
            )
            raise TypeError(
                f"The class `{model_class_qualname}` is not an orm mode object."
            )
        self.model_class = model_class

    def map_item(self, item):

        return self.model_class.from_orm(item)
