from runtool.utils import get_item_from_path, update_nested_dict


def compare_updated_nested_dict(data, to_update, expected):
    assert update_nested_dict(data, to_update) == expected


def test_updated_nested_dict_simple():
    compare_updated_nested_dict(
        data={"a": "hello"},
        to_update={"a": 1},
        expected={"a": 1},
    )


def test_updated_nested_dict_empty():
    compare_updated_nested_dict(
        data={"a": "hello"},
        to_update={},
        expected={"a": "hello"},
    )


def test_updated_nested_dict_empty_reversed():
    compare_updated_nested_dict(
        data={},
        to_update={"a": "hello"},
        expected={"a": "hello"},
    )


def test_updated_nested_dict_nested():
    compare_updated_nested_dict(
        data={"root": {"a": {"hello": "world"}}, "c": 1},
        to_update={"root": {"a": 10, "b": 20}},
        expected={"root": {"a": 10, "b": 20}, "c": 1},
    )


def test_updated_nested_dict_nested_reversed():
    compare_updated_nested_dict(
        data={"root": {"a": 10, "b": 20}},
        to_update={"root": {"a": {"hello": "world"}}, "c": 1},
        expected={"root": {"a": {"hello": "world"}, "b": 20}, "c": 1},
    )


def test_updated_nested_dict_complex():
    compare_updated_nested_dict(
        data={"a": 1, "b": 2, "c": {"d": {"d1": 1, "d2": 1}, "e": 1}},
        to_update={"c": {"d": {"d1": 2, "d2": 1}}},
        expected={"a": 1, "b": 2, "c": {"d": {"d1": 2, "d2": 1}, "e": 1}},
    )


def test_updated_nested_dict_complex_reversed():
    compare_updated_nested_dict(
        data={"c": {"d": {"d1": 2, "d2": 1}}},
        to_update={"a": 1, "b": 2, "c": {"d": {"d1": 1, "d2": 1}, "e": 1}},
        expected={"a": 1, "b": 2, "c": {"d": {"d1": 1, "d2": 1}, "e": 1}},
    )


def compare_get_item_from_path(data, path, expected):
    assert get_item_from_path(data, path) == expected


def test_get_item_from_path_simple():
    compare_get_item_from_path(
        data={"hello": [1, 2, 3, {"there": "world"}]},
        path="hello",
        expected=[1, 2, 3, {"there": "world"}],
    )


def test_get_item_from_path_medium():
    compare_get_item_from_path(
        data={"hello": [1, 2, 3, {"there": "world"}]},
        path="hello.3.there",
        expected="world",
    )
