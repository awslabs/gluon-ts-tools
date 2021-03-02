from runtool.recurse_config import (
    recursive_apply,
    recursive_apply_dict,
    recursive_apply_list,
    Versions,
)


def transform(node: dict):
    """
    Converts node to a version object if the node has a key "versions"
    else it multiplies the node by 2 if the node has key "double"
    """
    if "version" in node:
        return Versions(node["version"])
    elif "double" in node:
        return 2 * node["double"]
    return node


def compare_recursive_apply(node, expected, fn=transform):
    assert recursive_apply(node, fn) == expected


def test_recursive_apply_double_simple():
    compare_recursive_apply(
        node={"double": 1},
        expected=2,
    )


def test_recursive_apply_double_nested():
    compare_recursive_apply(
        node={
            "no_double": 2,
            "double_this": {"double": 2},
        },
        expected={"no_double": 2, "double_this": 4},
    )


def test_recursive_apply_versions():
    compare_recursive_apply(
        node={
            "my_list": [
                {"hello": "there"},
                {"a": {"version": [1, 2]}},
            ]
        },
        expected=Versions(
            [
                {"my_list": [{"hello": "there"}, {"a": 1}]},
                {"my_list": [{"hello": "there"}, {"a": 2}]},
            ]
        ),
    )


def test_recursive_apply_trivial():
    compare_recursive_apply({}, {})


def test_recursive_apply_merging_versions_simple():
    compare_recursive_apply(
        node=[Versions([1, 2])],
        expected=Versions([[1], [2]]),
        fn=lambda x: x,
    )


def test_recursive_apply_merging_versions_list():
    compare_recursive_apply(
        node=[Versions([1, 2]), Versions([3, 4])],
        expected=Versions([[1, 3], [1, 4], [2, 3], [2, 4]]),
        fn=lambda x: x,
    )


def test_recursive_apply_merging_versions_dict():
    compare_recursive_apply(
        node={"a": Versions([1, 2]), "b": Versions([3, 4])},
        expected=Versions(
            [
                {"a": 1, "b": 3},
                {"a": 1, "b": 4},
                {"a": 2, "b": 3},
                {"a": 2, "b": 4},
            ]
        ),
        fn=lambda x: x,
    )


def test_recursive_apply_merging_versions_list_in_dict():
    compare_recursive_apply(
        node={
            "a": [Versions([1, 2]), Versions([3, 4])],
            "b": [Versions([5, 6]), Versions([7, 8])],
        },
        expected=Versions(
            [
                {"a": [1, 3], "b": [5, 7]},
                {"a": [1, 3], "b": [5, 8]},
                {"a": [1, 3], "b": [6, 7]},
                {"a": [1, 3], "b": [6, 8]},
                {"a": [1, 4], "b": [5, 7]},
                {"a": [1, 4], "b": [5, 8]},
                {"a": [1, 4], "b": [6, 7]},
                {"a": [1, 4], "b": [6, 8]},
                {"a": [2, 3], "b": [5, 7]},
                {"a": [2, 3], "b": [5, 8]},
                {"a": [2, 3], "b": [6, 7]},
                {"a": [2, 3], "b": [6, 8]},
                {"a": [2, 4], "b": [5, 7]},
                {"a": [2, 4], "b": [5, 8]},
                {"a": [2, 4], "b": [6, 7]},
                {"a": [2, 4], "b": [6, 8]},
            ]
        ),
        fn=lambda x: x,
    )


def test_recursive_apply_merging_versions_list_in_list():
    compare_recursive_apply(
        node=[
            [Versions([1, 2]), Versions([3, 4])],
            [Versions([5, 6]), Versions([7, 8])],
        ],
        expected=Versions(
            [
                [[1, 3], [5, 7]],
                [[1, 3], [5, 8]],
                [[1, 3], [6, 7]],
                [[1, 3], [6, 8]],
                [[1, 4], [5, 7]],
                [[1, 4], [5, 8]],
                [[1, 4], [6, 7]],
                [[1, 4], [6, 8]],
                [[2, 3], [5, 7]],
                [[2, 3], [5, 8]],
                [[2, 3], [6, 7]],
                [[2, 3], [6, 8]],
                [[2, 4], [5, 7]],
                [[2, 4], [5, 8]],
                [[2, 4], [6, 7]],
                [[2, 4], [6, 8]],
            ]
        ),
        fn=lambda x: x,
    )


def test_recursive_apply_merging_versions_dict_in_dict():
    compare_recursive_apply(
        node={"a": {"b": Versions([1, 2])}, "c": Versions([2, 3])},
        expected=Versions(
            [
                {"a": {"b": 1}, "c": 2},
                {"a": {"b": 1}, "c": 3},
                {"a": {"b": 2}, "c": 2},
                {"a": {"b": 2}, "c": 3},
            ]
        ),
        fn=lambda x: x,
    )


def test_recursive_apply_merging_versions_with_function():
    compare_recursive_apply(
        node={
            "my_list": [
                {"hello": "there"},
                {"a": {"version": [1, 2]}},
                {"b": {"version": [3, 4]}},
            ]
        },
        expected=Versions(
            [
                {"my_list": [{"hello": "there"}, {"a": 1}, {"b": 3}]},
                {"my_list": [{"hello": "there"}, {"a": 1}, {"b": 4}]},
                {"my_list": [{"hello": "there"}, {"a": 2}, {"b": 3}]},
                {"my_list": [{"hello": "there"}, {"a": 2}, {"b": 4}]},
            ]
        ),
    )
