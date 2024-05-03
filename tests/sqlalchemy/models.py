from typing import Type

import sqlalchemy as sa
from sqlalchemy.orm.decl_api import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    metadata: sa.MetaData
    @declared_attr
    def id(cls: Type) -> "Mapped[sa.Integer]":
        value: Mapped[sa.Integer] = mapped_column(f"{cls.__name__.lower()}_id", sa.Integer, primary_key=True)
        return value

class TodoItem(Base):
    __tablename__ = "todos"

    title: Mapped[sa.String] = mapped_column(sa.String(100), nullable=False, index=True)
    text: Mapped[sa.Text | None] = mapped_column(sa.Text, index=True)
