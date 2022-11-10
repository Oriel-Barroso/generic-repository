# flake8: noqa F401

from .cached import CacheRepository
from .composition import MappedRepository
from .exceptions import CrudException, InvalidPayloadException, ItemNotFoundException
from .mapper import ConstructorMapper, LambdaMapper, Mapper, ToFunctionArgsMapper
from .repository import Repository

GenericBaseRepository = Repository
__all__ = [
    # Base classes
    "Repository",
    # Cache-based implementations:
    "CacheRepository",
    # Composition:
    "MappedRepository",
    "ConstructorMapper",
    "LambdaMapper",
    "Mapper",
    "ToFunctionArgsMapper",
    # Exceptions:
    "CrudException",
    "InvalidPayloadException",
    "ItemNotFoundException",
]

try:
    from .database import (
        DatabaseRepository,
        SqlalchemyMappedRepository,
        SqlalchemyModelRepository,
    )
except ImportError:  # pragma nocover
    pass
else:
    __all__ += [
        "DatabaseRepository",
        "SqlalchemyMappedRepository",
        "SqlalchemyModelRepository",
    ]

try:
    from .http import HttpRepository
except ImportError:  # pragma nocover
    pass
else:
    __all__ += ["HttpRepository"]

try:
    from .pydantic import PydanticDictMapper, PydanticObjectMapper
except ImportError:  # pragma nocover
    pass
else:
    __all__ += ["PydanticDictMapper", "PydanticObjectMapper"]
