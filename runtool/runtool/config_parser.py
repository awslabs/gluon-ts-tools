import itertools
import math
import re
from functools import partial, singledispatch
from uuid import uuid4

from runtool.datatypes import Versions
from runtool.runtool import DotDict
from runtool.utils import update_nested_dict

from typing import Callable, Any


def get(data, path):
    """
    Access dict or list using a path split by '.'
    """
    for key in path.split("."):
        data = data[key]
    return data


@singledispatch
def recursive_apply(node, fn: Callable) -> Any:
    """
    Base case of singledispatch function for leaf nodes.
    """
    return node


@recursive_apply.register
def recursive_apply_dict(node: dict, fn):
    """
    Applies 'fn' to each element in the dict.
    """
    # if fn changes the node, return the changes
    after_function = fn(node)
    if after_function is not node:
        return after_function

    # else merge children of type Versions into a new version to be returned
    # i.e: {'a':Versions([1,2]) 'b':Versions([3,4])}
    # becomes
    # [(('a',1), ('a',2)), (('b',3), ('b',4))]
    # and then
    # [
    #   {'a':1, 'b':3},
    #   {'a':1, 'b':4},
    #   {'a':2, 'b':3},
    #   {'a':2, 'b':4}
    # ]
    expanded_children = []
    children = {}
    for key in node:
        child = recursive_apply(node[key], fn)
        if type(child) is Versions:
            expanded_children.append(itertools.product([key], child.versions))
        else:
            children[key] = child
    as_dicts = [dict(ver) for ver in itertools.product(*expanded_children)]

    # sanity check
    if as_dicts == [{}]:
        return children

    for dct in as_dicts:
        dct.update(children)
    return Versions(as_dicts)


@recursive_apply.register
def recursive_apply_list(node: list, fn):
    child_versions = []
    child_normal = [None] * len(node)
    for index in range(len(node)):
        child = recursive_apply(node[index], fn)
        if isinstance(child, Versions):
            # child = Versions([1,2])
            # =>
            # expanded_child_version = ((index, 1), (index, 2))
            expanded_child_version = itertools.product([index], child.versions)
            child_versions.append(expanded_child_version)
        else:
            child_normal[index] = child

    if len(child_versions) == 0:
        return child_normal
    # for node with two Version elements Version([1,2]) on index 1
    # and Version([3,4]) on index 3
    # merged_versions = [
    #   ((1,1), (3,4)),
    #   ...
    #   ((1,2), (3,5))
    # ]
    merged_versions = itertools.product(*child_versions)

    new_versions = []
    for version in merged_versions:
        new_data = child_normal[:]  # copy list
        for index, value in version:
            new_data[index] = value
        new_versions.append(new_data)

    return Versions(new_versions)


# APPLY: Apply the transformation to the data
def apply_from(node, data):
    node = dict(**node)
    path = node.pop("$from")
    from_value = get(data, path)
    from_value = recursive_apply(from_value, partial(do_from, context=data))

    assert isinstance(
        from_value, dict
    ), "$from can only be used to inherit from a dict"
    from_value = update_nested_dict(from_value, node)
    return dict(**from_value)


def apply_ref(node, context):
    assert len(node) == 1, "$ref needs to be only value"
    data = get(context, node["$ref"])
    return recursive_apply(data, partial(do_ref, context=context))


def evaluate(text, locals):
    uid = str(uuid4()).split("-")[-1]
    locals = {**DotDict(locals)}
    globals = {**math.__dict__, "uid": uid}
    ret = eval(
        text,
        globals,
        locals,
    )
    if isinstance(ret, dict) and "$eval" in ret:
        return do_eval(ret, locals)
    return ret


def recurse_trial(path, data):
    tmp = data
    current_path = []
    path = path.replace("[", ".").replace("]", "").replace('"', "")
    for key in path.split("."):
        try:
            tmp = tmp[key]
            current_path.append(key)
        except:
            break

    return ".".join(current_path), do_trial(tmp, data)


def apply_trial(node, locals):
    assert len(node) == 1, "$eval needs to be only value"
    text = str(node["$eval"])

    # dict used to remove duplicates
    matches = {
        text[item.start() : item.end()]: None
        for item in re.finditer(
            r"(__trial__(?:(?:\[[0-9]+\])|(?:\[(?:\'|\")[a-zA-Z_0-9$]+(?:\'|\")\])|(?:\.[a-zA-Z_0-9]+))+)",
            text,
        )
    }

    # find longest working path for each match in locals
    for path in matches:
        substring, value = recurse_trial(path, locals)

        if isinstance(value, dict) and "$eval" in value:
            raise TypeError("$eval: $trial cannot resolve to value")
        elif type(value) is str:
            text = text.replace(substring, f"'{value}'")
        else:
            text = text.replace(substring, str(value))

    return evaluate(text, locals)


def recurse_eval(path, data):
    # since values such as a.b.split() is allowed.
    # we need to identify what are values in the dict
    # thus here we fetch as much info from the dict as possible
    # stopping whenever an unknown key is found
    tmp = data
    current_path = ["$"]
    path = path.replace("[", ".[")
    for key in path.split("."):
        try:
            original_key = key
            if "[" in key:
                key = key.replace("[", "").replace("]", "").replace('"', "")
            tmp = tmp[key]
            current_path.append(original_key)
        except:
            break
    return ".".join(current_path).replace(".[", "["), do_eval(tmp, data)


def apply_eval(node, locals):
    assert len(node) == 1, "$eval needs to be only value"
    text = str(node["$eval"])
    text = text.replace("$trial", "__trial__")

    # find all matches of $.somestring.somotherstring[0]['dsd']["sdasda"] ...
    matches = {
        text[item.start() : item.end()]: text[item.start() + 2 : item.end()]
        for item in re.finditer(
            r"(\$(?:(?:\[[0-9]+\])|(?:\[(?:\'|\")[a-zA-Z_0-9$]+(?:\'|\")\])|(?:\.[a-zA-Z_0-9]+))+)",
            text,
        )
    }

    for path in matches.values():
        current_path, value = recurse_eval(path, locals)
        if isinstance(value, dict) and "$eval" in value:
            text = text.replace(current_path, f"({value['$eval']})")
        elif type(value) is str:
            text = text.replace(current_path, f"'{value}'")
        else:
            text = text.replace(current_path, str(value))

    try:
        return evaluate(text, locals)
    except NameError as error:
        if "__trial__" in str(error):
            node["$eval"] = text
            return node
        else:
            raise error


def apply_each(node, context):
    # should return th different versions
    # item.e. $each: [1,2] should return two versions in an array

    each = recursive_apply(
        node.pop("$each"), partial(do_each, context=context)
    )
    if isinstance(each, list):
        # check if all are dicts or has the $None tag
        if all(
            map(lambda item: isinstance(item, dict) or item == "$None", each)
        ):
            new = []
            for item in each:
                if item == "$None":
                    new.append(node)
                else:
                    item.update(node)
                    new.append(item)
            each = new
        else:
            each = [item if not item == "$None" else None for item in each]
        return Versions(each)
    elif isinstance(each, dict):
        seperated_dicts = [{key, val} for key, val in each.items()]
        for a_dict in seperated_dicts:
            a_dict.update(node)
        return Versions(seperated_dicts)
    elif isinstance(each, Versions):
        # when having a nested $each this will be triggered
        flattened = itertools.chain.from_iterable(each.versions)
        return Versions(list(flattened))
    else:
        print("Something went wrong when expanding $each")
        raise NotImplementedError


# DO: find correct place within the data to do the transformation
def do_from(node, context):
    if isinstance(node, dict) and "$from" in node:
        return apply_from(node, context)
    return node


def do_ref(node, context):
    if isinstance(node, dict) and "$ref" in node:
        return apply_ref(node, context)
    return node


def do_eval(node, locals):
    if isinstance(node, dict) and "$eval" in node:
        return apply_eval(node, locals)
    return node


def do_trial(node, locals):
    if isinstance(node, dict) and "$eval" in node:
        return apply_trial(node, locals)
    return node


def do_each(node, context):
    if isinstance(node, dict) and "$each" in node:
        return apply_each(node, context)
    return node


def to_list(data):
    if type(data) is Versions:
        return data.versions
    else:
        return [data]


def apply_transformations(data):
    data = recursive_apply(data, partial(do_from, context=data))
    data = recursive_apply(data, partial(do_eval, locals=data))
    data = recursive_apply(data, partial(do_each, context=data))
    data = [
        recursive_apply(item, partial(do_ref, context=item))
        for item in to_list(data)
    ]
    return data
