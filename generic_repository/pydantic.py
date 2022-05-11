from typing import Any, Generic, Type, TypeVar

import pydantic

from .mapper import Mapper

_Model = TypeVar("_Model", bound=pydantic.BaseModel)


class PydanticDictMapper(Mapper[_Model, dict], Generic[_Model]):
    def __init__(self, *model_classes: Type[_Model]) -> None:
        for cls in model_classes:
            assert issubclass(cls, pydantic.BaseModel)

        super().__init__()

        self.model_classes = model_classes

    def map_item(self, item: _Model, **kwargs) -> dict:
        if not any(map(lambda x: isinstance(item, x), self.model_classes)):
            raise AssertionError("The pased object isnot of any provided class.")

        return item.dict(**kwargs)


class PydanticObjectMapper(Mapper[Any, _Model], Generic[_Model]):
    def __init__(self, model_class: Type[_Model]) -> None:
        self.model_class = model_class

    def map_item(self, item, **kwargs: Any):
        assert self.model_class.Config.orm_mode
        return self.model_class.from_orm(item)
