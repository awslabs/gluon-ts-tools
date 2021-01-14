from collections.abc import Mapping

from runtool.datatypes import Versions


def recurse_print(data, indent=0, step_size=3):
    ind = " " * indent
    if isinstance(data, dict):
        print(ind, "{")
        for key, value in data.items():
            print(ind, key, "\r")
            recurse_print(value, indent + step_size)
        print(ind, "},")
    elif isinstance(data, list):
        print(ind, "[")
        for item in data:
            recurse_print(item, indent + step_size)
        print(ind, "],")
    elif type(data) is Versions:
        print(ind, "[")
        for item in data.versions:
            recurse_print(item, indent + step_size)
        print(ind, "],")
    else:
        print("\r", ind, data)


def update_nested_dict(data, to_update):
    for key, value in to_update.items():
        if isinstance(data, Mapping):
            if isinstance(value, Mapping):
                data[key] = update_nested_dict(data.get(key, {}), value)
            else:
                data[key] = to_update[key]
        else:
            data = {key: to_update[key]}
    return data
