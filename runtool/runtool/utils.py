from typing import Union, Any


def get_item_from_path(data: Union[dict, list], path: str) -> Any:
    """
    Access dict or list using a path split by '.'

    Example:
    >>> get_item_from_path(
    ...     {
    ...         "hello": [1, 2, 3, {"there": "world"}]
    ...     },
    ...     "hello.3.there"
    ... )
    'world'

    Returns
    -------
    Any
        The value of `data` at the given `path`
    """
    for key in path.split("."):
        try:
            data = data[key]
        except TypeError:
            data = data[int(key)]
    return data


def update_nested_dict(data: dict, to_update: dict) -> dict:
    """
    Returns an updated version of the `data` dict updated with any changes from the `to_update` dict.
    This behaves differently from the builting`dict.update` method, see the example below.

    Example using `update_nested_dict`:

    >>> data = {"root": {"smth": 10, "smth_else": 20}}
    >>> to_update = {"root": {"smth": {"hello" : "world"}}}
    >>> update_nested_dict(data, to_update)
    {'root': {'smth': {'hello': 'world'}, 'smth_else': 20}}

    Example using the builtin `dict.update`:
    >>> data.update(to_update)
    >>> print(data)
    {'root': {'smth': {'hello': 'world'}}}

    Parameters
    ----------
    data
        The base dictionary which should be updated.
    to_update
        The changes which should be added to the data.
    Returns
    -------
    dict
        The updated dictionary.
    """
    for key, value in to_update.items():
        if isinstance(data, dict):
            if isinstance(value, dict):
                data[key] = update_nested_dict(data.get(key, {}), value)
            else:
                data[key] = to_update[key]
        else:
            data = {key: to_update[key]}
    return data
