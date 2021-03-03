import re
from functools import partial
from typing import Any, Callable, Tuple
from uuid import uuid4

from runtool.datatypes import DotDict
from runtool.recurse_config import Versions, recursive_apply
from runtool.utils import get_item_from_path, update_nested_dict
from collections import UserDict


def apply_from(node: dict, context: dict) -> dict:
    """
    Update the node with the data which the path in node['$from'] is pointing to in the context dictionary.
    i.e.

    >>> apply_from(
    ...     node={"$from": "another_node.a_key", "some_key": "some_value"},
    ...     context={"another_node": {"a_key": {"hello": "world"}}}
    ... )
    {'hello': 'world', 'some_key': 'some_value'}

    Parameters
    ----------
    node
        The node which should be processed.
    context:
        Data which can be referenced by the path in node["$from"].
    Returns
    -------
    Dict
        the `node` updated with values from `context[node["from"]]`
    """
    if not (isinstance(node, dict) and "$from" in node):
        return node

    source = get_item_from_path(context, node.pop("$from"))

    # resolve any $from in the node we inherit from
    # this is to avoid updating the node with a new $from
    source = recursive_apply(source, partial(apply_from, context=context))

    assert isinstance(
        source, dict
    ), "$from can only be used to inherit from a dict"

    return update_nested_dict(source, node)


def apply_ref(node: dict, context: dict) -> Any:
    """
    If the node contains a `$ref`, resolve any nested `$ref` which node["$ref"]
    points to in the `context`. Thereafter replace the current node with the
    resolved value.

    In the below example, we want to replace the node with the value of
    `context["some_node"][0]["some_val"]`. This, however references
    `context["target"]` thus the value which the node will be replaced with
    will be `1` when the nested references has been resolved.

    >>> apply_ref(
    ...     node={"$ref": "some_node.0.some_val"},
    ...     context={
    ...         "target": 1,
    ...         "some_node": [
    ...             {"some_val": {"$ref": "target"}},
    ...             "ignored"
    ...         ]
    ...     }
    ... )
    1

    Parameters
    ----------
    node
        The node which should be processed.
    context
        The data which can be referenced using $ref
    Returns
    -------
    Any
        The data which is referenced
    """
    if not (isinstance(node, dict) and "$ref" in node):
        return node

    assert len(node) == 1, "$ref needs to be the only value"
    data = get_item_from_path(context, node["$ref"])
    return recursive_apply(data, partial(apply_ref, context=context))


def evaluate(expression: str, locals: dict) -> Any:
    """
    Performs the python function `eval` using the `expression`.
    The evaluated expression will have access to the values in `locals`
    when `eval` is applied as well as to a unique id `uid`.

    >>> evaluate(
    ...     expression="len(uid) + some_value",
    ...     locals={"some_value": 2}
    ... )
    14

    Parameters
    ----------
    expression
        The expression which should be evaluated
    locals
        The locals parameter to the `eval` function in the standard library.
    Returns
    -------
    Any
        The value after applying `eval` to the expression.
    """
    return eval(
        expression,
        dict(uid=str(uuid4()).split("-")[-1]),
        dict(DotDict(locals)),
    )


def recurse_eval(path: str, data: dict, fn: Callable) -> Tuple[str, Any]:
    """
    Given a `path` such as `a.b.0.split(' ')` this function traverses
    the `data` dictionary using the path, stopping whenever a key cannot be
    found in the `data`. `fn` is then applied to the extracted data and the
    result is returned along with the part of the path which was traversed.

    In the following example, `a.b.0` is identified as the path to return
    since `.split()` is not an item in `data`.

    >>> recurse_eval(
    ...     path="a.b.0.split(' ')",
    ...     data={"a": {"b": [{"$eval": "'hey ' * 2"}]}},
    ...     fn=lambda node, _ : eval(node["$eval"]) if "$eval" in node else node
    ... )
    ('a.b.0', 'hey hey ')

    Parameters
    ----------
    path
        The path to fetch from in the data
    data
        Dictionary which should be traversed using the path
    fn
        function to call with the fetched data as parameter
    Returns
    -------
    Tuple[str, Any]
        The path and the value after applying the `fn`
    """
    tmp = data
    current_path = []
    path = path.replace("[", ".[")
    for key in path.split("."):
        original_key = key
        if "[" in key:
            key = key.replace("[", "").replace("]", "").replace('"', "")
        try:
            tmp = tmp[key]
            current_path.append(original_key)
        except TypeError:
            try:
                tmp = tmp[int(key)]
                current_path.append(original_key)
            except ValueError:
                break
        except:
            break
    return ".".join(current_path).replace(".[", "["), fn(tmp, data)


def apply_eval(node: dict, locals: dict) -> Any:
    """
    Evaluates the expression in `node["$eval"]` recursively then returns
    the result.

    The text in `node["$eval"]` can contain some keywords which `apply_eval`
    can use to preprocess the text before `eval` is run on the text.
    The following keywords are supported in the text:

    - `$`       is used to reference data in the `locals` parameters
    - `$trial`  references an experiment which is defined during runtime
                (see `apply_trial`)

    Example of when `$` is used:

    >>> apply_eval({"$eval": "2 + 5 * $.value"}, {"value": 2})
    12

    >>> apply_eval({"$eval": "$.my_key.split()"}, {"my_key": "some string"})
    ['some', 'string']

    Example of when `$trial` is used. Since we do not yet know what the `$trial`
    should resolve to we cannot calculate the value.
    Note::

        $trial gets renamed to __trial__ here as this function is a
        preprocessing step to `apply_trial`.

    >>> apply_eval({"$eval": "$trial.algorithm.some_value * 2"}, {})
    {'$eval': '__trial__.algorithm.some_value * 2'}

    Parameters
    ----------
    node
        The node which should be processed.
    locals:
        The local variables available for when calling eval.
    Returns
    -------
    Any
        The transformed node.
    """
    if not (isinstance(node, dict) and "$eval" in node):
        return node

    assert len(node) == 1, "$eval needs to be only value"
    text = str(node["$eval"])
    text = text.replace("$trial", "__trial__")

    # matches any parts of the text which is similar to this:
    # $.somestring.somotherstring[0]['a_key']["some_key"]
    regex = r"""
        (\$                         # match string starting with $ and followed by:
            (?:
                \[[\d]+\]|          # digits enclosed in [] i.e. $[0]
                \[\"[\w_\d$]+\"\]|  # words or digits in "[]" i.e. $["0"]
                \[\'[\w_\d$]+\'\]|  # words or digits in '[]' i.e. $['0']
                \.[\w_\d]+          # words or digits prepended with a dot, i.e. $.hello
            )+
        )
    """

    # replace any matched substrings of the text with whatever the
    # substrings pointed to in the locals parameter
    for match in re.finditer(regex, text, flags=re.VERBOSE):
        path, value = recurse_eval(match[0].lstrip("$."), locals, apply_eval)
        path = f"$.{path}"
        if isinstance(value, dict) and "$eval" in value:
            text = text.replace(path, f"({value['$eval']})")
        elif type(value) is str:
            text = text.replace(path, f"'{value}'")
        else:
            text = text.replace(path, str(value))

    try:
        # continue recursion as to handle any $eval nodes
        # generated after evaluating the current node.
        return apply_eval(evaluate(text, locals), locals)
    except NameError as error:
        if "__trial__" in str(error):
            node["$eval"] = text
            return node
        else:
            raise error


def apply_trial(node: dict, locals: dict) -> Any:
    """
    Works similarly as `apply_eval` however this method only evaluates
    the parts of `node["$eval"]` which starts with __trial__.
    For more information read the documentation of `apply_eval`.

    >>> apply_trial(
    ...     {"$eval" : "2 + __trial__.something[0]"},
    ...     {"__trial__": {"something":[1,2,3]}}
    ... )
    3

    Parameters
    ----------
    node
        The node which should be processed.
    locals:
        The local variables available for when calling eval.
    Returns
    -------
    Any
        The transformed node.
    """
    if not (isinstance(node, (dict, UserDict)) and "$eval" in node):
        return node

    assert len(node) == 1, "$eval needs to be only value"
    text = str(node["$eval"])

    regex = r"""
        (__trial__
            (?:
                \[[\d]+\]|          # digits enclosed in [] i.e. __trial__[0]
                \[\"[\w_\d$]+\"\]|  # words or digits in "[]" i.e. __trial__["0"]
                \[\'[\w_\d$]+\'\]|  # words or digits in '[]' i.e. __trial__['0']
                \.\w+[\w_\d]*       # words or digits prepended with a dot, i.e. __trial__.hell0
            )+
        )
    """

    # find longest working path for each match in locals
    for match in re.finditer(regex, text, flags=re.VERBOSE):
        substring, value = recurse_eval(match[0], locals, apply_trial)

        if isinstance(value, dict) and "$eval" in value:
            raise TypeError("$eval: $trial cannot resolve to value")
        elif type(value) is str:
            text = text.replace(substring, f"'{value}'")
        else:
            text = text.replace(substring, str(value))

    # continue recursion as to handle any $eval nodes
    # generated after evaluating the current node.
    return apply_eval(evaluate(text, locals), locals)


def apply_each(node: dict) -> Versions:
    """
    If `$each` is in the node, it means that the node can become
    several different values.

    NOTE::
        nodes which can take multiple values are represented as
        `runtool.datatypes.Versions` objects. Refer to their documentation
        for further information.

    Example, a node which can take the values `1` or `2` or `3` can be generated
    as follows:

    >>> apply_each({"$each":[1,2,3]})
    Versions([1, 2, 3])

    If dictionaries are passed to $each, these will be updated with the
    value of the passed `node` before a Versions object is generated.

    >>> apply_each({"a": 1, "$each": [{"b": 2}, {"b": 3}]})
    Versions([{'b': 2, 'a': 1}, {'b': 3, 'a': 1}])

    It is possible to have an unaltered version of the parent node by
    inserting $None into the values of $each. In the example below,
    apply_each generates two versions of the node, one which is unaltered
    and one which is merged with another dict.

    >>> apply_each({"a": 1, "$each": ["$None", {"b": 2}]})
    Versions([{'a': 1}, {'b': 2, 'a': 1}])

    Below is a more complicated example combining the two examples above:

    >>> apply_each(
    ...     {
    ...         "a": 1,
    ...         "$each": ["$None", {"b": 2, "c": 3}]
    ...     }
    ... )
    Versions([{'a': 1}, {'b': 2, 'c': 3, 'a': 1}])

    Parameters
    ----------
    node
        The node which should have `$each` applied to it.

    Returns
    -------
    runtool.datatypes.Versions
        The versions object representing the different values of the node.
    """
    if not (isinstance(node, dict) and "$each" in node):
        return node

    each = node.pop("$each")
    if not isinstance(each, list):
        raise TypeError(
            f"$each requires a list, not an object of type {type(each)}"
        )

    # Generate versions of the current node
    versions = []
    for item in each:
        if item == "$None":
            # return unaltered node
            # node = {"a": 1, "$each": ["$None"]}
            # ==>
            # {"a": 1}
            versions.append(node)
        elif isinstance(item, dict):
            # merge node with value in $each
            # node = {"a": 1, "$each": [{"b: 2"}]}
            # ==>
            # {"a": 1, "b": 2}
            item.update(node)
            versions.append(item)
        else:
            # any other value overwrites the node if node is
            # otherwise empty.
            # node = {"$each": [2]}
            # ==>
            # 2
            if node:
                node["$each"] = each
                raise TypeError(
                    "Using $each in a non-empty node is only supported"
                    " when using dictionaries or with the $None operator."
                    f" The error occured in:\n{node}"
                )
            versions.append(item)
    return Versions(versions)
