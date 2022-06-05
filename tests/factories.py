import factory

from .sqlalchemy import models
from .todos import AddTodoPayload


class TodoItemModelFactory(factory.Factory):
    title = factory.Faker("sentence")

    class Meta:
        model = models.TodoItem


class AddTodoFactory(TodoItemModelFactory):
    class Meta:
        model = AddTodoPayload


class TodoDataFactory(TodoItemModelFactory):
    class Meta:
        model = dict
