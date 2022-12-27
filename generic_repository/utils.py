import typing


class MergeError(Exception):
    def __init__(self, location: typing.List[typing.Any], message: str) -> None:
        super().__init__(f"Error at {'->'.join(map(str, location))}: {message}")


def merge_dicts(*dicts: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    """Merge two or more dicts into new one.

    Returns:
        typing.Dict[str, typing.Any]: The resulting dictionary.

    A simple merge example:
    >>> merge_dicts({'a': 1}, {'b': 2})
    {'a': 1, 'b': 2}
    >>>

    For a nested merge:
    >>> dict_a={'x': {'a': 1}}
    >>> dict_b={'x': {'b': 1}}
    >>> result = merge_dicts(dict_a, dict_b)
    >>> result == {'x': {'a': 1, 'b': 1}}
    True
    >>>
    """
    result = _merge_dicts(*dicts)

    return result


def _merge_dicts(  # noqa C901
    *dicts: typing.Dict[str, typing.Any],
    location: typing.Optional[typing.List[typing.Any]] = None,
) -> typing.Dict[str, typing.Any]:
    result: typing.Dict[str, typing.Any] = {}
    current_key = []
    if location is not None:
        current_key += location

    for i, source in enumerate(dicts):
        current_key.append(i)
        for key, value in source.items():
            current_key.append(key)
            current = result.get(key, None)

            if isinstance(current, dict):
                if not isinstance(value, dict):
                    raise MergeError(
                        current_key.copy(),
                        "Type mismatch: The right value is not a dict.",
                    )
                result[key] = _merge_dicts(current, value, location=current_key)
            elif isinstance(current, list):
                if isinstance(value, (set, tuple, list)):
                    result[key] = current + [*value]
                else:
                    result[key] = current + [value]
            else:
                result[key] = value

            current_key.pop()

        current_key.pop()

    return result
