from runtool.recurse_config import Versions
from runtool.transformations import (
    apply_each,
    apply_eval,
    apply_from,
    apply_ref,
    apply_trial,
    evaluate,
    recurse_eval,
)


def compare_apply_from(node, data, expected):
    assert apply_from(node, data) == expected


def compare_apply_ref(node, context, expected):
    assert apply_ref(node, context) == expected


def compare_apply_trial(text, locals, expected):
    assert apply_trial(text, locals) == expected


def compare_apply_each(node, expected):
    assert apply_each(node) == expected


def test_apply_from_simple():
    compare_apply_from(
        node={
            "$from": "b",
            "some_key": "some_value",
        },
        data={
            "b": {
                "a": {"hello": "world"},
            },
        },
        expected={
            "a": {"hello": "world"},
            "some_key": "some_value",
        },
    )


def test_apply_from_empty():
    compare_apply_from(
        node={
            "$from": "b",
            "some_key": "some_value",
        },
        data={
            "b": {},
        },
        expected={
            "some_key": "some_value",
        },
    )


def test_apply_from_with_path():
    compare_apply_from(
        node={
            "$from": "b.c.0",
            "some_key": "some_value",
        },
        data={
            "b": {
                "c": [{"hello": "world"}],
            },
        },
        expected={
            "hello": "world",
            "some_key": "some_value",
        },
    )


def test_apply_ref_simple():
    compare_apply_ref(
        node={"$ref": "a"},
        context={"target": 1, "a": "hello"},
        expected="hello",
    )


def test_apply_ref_nested():
    compare_apply_ref(
        node={"$ref": "a.0.b"},
        context={
            "target": 1,
            "a": [{"b": {"$ref": "target"}}, "ignored"],
        },
        expected=1,
    )


def test_evaluate():
    assert (
        evaluate(
            expression="2 + 2",
            locals={},
        )
        == 4
    )


def test_evaluate_with_mathlib_and_locals():
    assert (
        evaluate(
            expression="len(uid) + some_value",
            locals={"some_value": 2},
        )
        == 14
    )


def test_recurse_eval():
    def simple_eval(node, context):
        return eval(node["$eval"]) if "$eval" in node else node

    assert (
        recurse_eval(
            path="a.b.0.split(' ')",
            data={"a": {"b": [{"$eval": "'hey ' * 2"}]}},
            fn=simple_eval,
        )
        == ("a.b.0", "hey hey ")
    )


def compare_apply_eval(text, locals, expected):
    assert apply_eval(text, locals) == expected


def test_apply_eval_simple():
    compare_apply_eval(
        text={"$eval": "2 + 2"},
        locals={},
        expected=4,
    )


def test_apply_eval_referencing_locals():
    compare_apply_eval(
        text={"$eval": "2 + 5 * $.value"},
        locals={"value": 2},
        expected=12,
    )


def test_apply_eval_with_trial():
    compare_apply_eval(
        text={"$eval": "$trial.algorithm.some_value * 2"},
        locals={},
        expected={"$eval": "__trial__.algorithm.some_value * 2"},
    )


def test_apply_eval_with_trial_and_dollar():
    compare_apply_eval(
        text={"$eval": "$trial.algorithm.some_value * $.some_value"},
        locals={"some_value": 2},
        expected={"$eval": "__trial__.algorithm.some_value * 2"},
    )


def test_apply_trial_simple():
    compare_apply_trial(
        text={"$eval": "2 + __trial__.something[0]"},
        locals={"__trial__": {"something": [1, 2, 3]}},
        expected=3,
    )


def test_apply_each_simple():
    compare_apply_each(
        node={"$each": [1, 2, 3]},
        expected=Versions([1, 2, 3]),
    )


def test_apply_each_with_none():
    compare_apply_each(
        node={
            "c": "dummy",
            "$each": [
                "$None",
                {"a": 150, "b": 64},
            ],
        },
        expected=Versions(
            [
                {"c": "dummy"},
                {"a": 150, "b": 64, "c": "dummy"},
            ]
        ),
    )
