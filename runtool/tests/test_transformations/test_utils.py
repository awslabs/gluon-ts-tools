# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

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
