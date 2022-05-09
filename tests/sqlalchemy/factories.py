import factory

from . import models
from .repository import AddTodoPayload


class TodoItemModelFactory(factory.Factory):
    title = factory.Faker("sentence")

    class Meta:
        model = models.TodoItem


class AddTodoFactory(TodoItemModelFactory):
    class Meta:
        model = AddTodoPayload
