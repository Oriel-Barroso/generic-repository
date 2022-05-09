import sqlalchemy as sa
from sqlalchemy.orm.decl_api import as_declarative, declared_attr


@as_declarative()
class Base:
    metadata: sa.MetaData

    @declared_attr
    def id(cls) -> "sa.Column[sa.Integer]":
        return sa.Column(f"{cls.__name__.lower()}_id", sa.Integer, primary_key=True)


class TodoItem(Base):
    __tablename__ = "todos"

    title = sa.Column(sa.String(100), nullable=False, index=True)
    text = sa.Column(sa.Text, index=True)
