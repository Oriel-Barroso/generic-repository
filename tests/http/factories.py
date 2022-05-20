from factory import DictFactory, Faker


class TodoItemDataFactory(DictFactory):
    """A todo item payload factory.

    >>> data = TodoItemDataFactory()
    >>> data
    {...}
    >>>
    """

    title = Faker("sentence")
    body = Faker("paragraph")
    complete = Faker("pybool")
