from pathlib import Path

import pytest
import yaml
from runtool.transformer import apply_transformations


def assert_config_equal(source, expected):
    received = apply_transformations(yaml.safe_load(source))
    assert received == yaml.safe_load(expected)


def load(testname):
    # find data folder ./../test_data/<testname>
    path = Path(__file__).parent / "test_data" / testname

    expected_path = path / "expected.yml"
    source_path = path / "source.yml"

    with source_path.open() as source, expected_path.open() as expected:
        return {
            "source": source.read(),
            "expected": expected.read(),
        }


def test_from_simple():
    assert_config_equal(
        source="""
        base:
            data: 1
        inherited:
            $from: base""",
        expected="""
        - base:
            data: 1
          inherited:
            data: 1""",
    )


def test_from_double_inheritance():
    assert_config_equal(
        source="""
        base: 
            data: 1
        inherited_1: 
            $from: base
        inherited_2: 
            $from: inherited_1""",
        expected="""
        - base:
            data: 1
          inherited_1: 
            data: 1
          inherited_2: 
            data: 1""",
    )


def test_from_overriding_variables():
    assert_config_equal(
        source="""
        base:
            data: 1
            new: 1
        inherited:
            $from: base
            new: 2
        """,
        expected="""
        - base:
            data: 1
            new: 1
          inherited:
            data: 1
            new: 2
        """,
    )


def test_from_overriding_variables_nested():
    assert_config_equal(
        source="""
        base:
            data: 1
            new: 
                a: 1
        inherited:
            $from: base
            new: 
                b: 2
        """,
        expected="""
        - 
            base:
                data: 1
                new: 
                    a: 1
            inherited:
                data: 1
                new: 
                    a: 1
                    b: 2
        """,
    )


def test_from_adding_variables():
    assert_config_equal(
        source="""
        base:
            data: 1
        inherited:
            $from: base
            new: 2
        """,
        expected="""
        - base:
            data: 1
          inherited:
            data: 1
            new: 2
        """,
    )


def test_ref():
    assert_config_equal(
        source="""
        ref:
            $ref: source
        source: 10
        """,
        expected="""
        - ref: 10
          source: 10""",
    )


def test_ref_double():
    assert_config_equal(
        source="""
        first: 
            $ref: source
        second:
            $ref: first
        source: 10
        """,
        expected="""
        - first: 10
          second: 10
          source: 10
        """,
    )


def test_from_ref():
    assert_config_equal(
        source="""
        source:
            inherited_value: 1
        from_ref:
            $from: source
            referenced_value:
                $ref: to_ref
        to_ref: 0
        """,
        expected="""
        - source:
            inherited_value: 1
          from_ref:
            inherited_value: 1
            referenced_value: 0
          to_ref: 0
        """,
    )


def test_each_simple():
    assert_config_equal(
        source="""
        my_each:
            $each: [1,2,3]
        """,
        expected="""
        - my_each: 1
        - my_each: 2
        - my_each: 3
        """,
    )


def test_each_nested():
    assert_config_equal(
        source="""
        my_each:
            $each:
                - $each: [1,2,3]
        """,
        expected="""
        - my_each: 1
        - my_each: 2
        - my_each: 3
        """,
    )


def test_each_nested_static_variables():
    assert_config_equal(
        source="""
        my_each:
            number: 
                $each: [1,2,3]
            static: dummy
        """,
        expected="""
        - my_each: 
            number: 1
            static: dummy
        - my_each: 
            number: 2
            static: dummy
        - my_each: 
            number: 3
            static: dummy
        """,
    )


def test_each_nested_static_variables_2():
    assert_config_equal(
        source="""
        my_each: 
                $each: [1,2,3]
        static: dummy
        """,
        expected="""
        - 
            my_each: 1
            static: dummy
        - 
            my_each: 2
            static: dummy
        - 
            my_each: 3
            static: dummy
        """,
    )


def test_each_multiple():
    assert_config_equal(
        source="""
        base:
            - $each: [1,2]
            - $each: [3,4]""",
        expected="""
        - base:
            - 1
            - 3
        - base:
            - 1
            - 4
        - base:
            - 2
            - 3
        - base:
            - 2
            - 4""",
    )


def test_each_existing_values():
    assert_config_equal(
        source="""
        hello:
            $each:
                - new_1: 1
                - new_2: 2
            should_remain: there
        """,
        expected="""
        - hello:
            new_1: 1
            should_remain: there
        - hello:
            new_2: 2
            should_remain: there    
        """,
    )


def test_each_simple_hyperparameters():
    assert_config_equal(
        source="""
        hyperparameters:
            context_length:
                $each: [7,14]
            freq: D
            prediction_length:
                $each: [7, 14]
        """,
        expected="""
        - hyperparameters:
            context_length: 7
            freq: D
            prediction_length: 7 
        - hyperparameters:
            context_length: 7
            freq: D
            prediction_length: 14 
        - hyperparameters:
            context_length: 14
            freq: D
            prediction_length: 7 
        - hyperparameters:
            context_length: 14
            freq: D
            prediction_length: 14 
        """,
    )


def test_each_complex():
    assert_config_equal(
        source="""
        hyperparameters:
            forecaster_name: dummy
            $each:
                - epochs: 5
                - epochs: 150
                  batch_size: 64
        """,
        expected="""
        - hyperparameters:
            forecaster_name: dummy
            epochs: 5
        - hyperparameters:
            forecaster_name: dummy
            epochs: 150
            batch_size: 64
        """,
    )


def test_each_ref():
    """
    $ref should not cause $each to
    generate versions multiple times
    """
    assert_config_equal(
        source="""
        my_algorithm: 
            $name: 
                $each:
                    - my first name
                    - the second name

        my_algos:
            - $ref: my_algorithm
        """,
        expected="""
        - 
            my_algorithm: 
                $name: my first name
            my_algos: 
                - $name: my first name
        - 
            my_algorithm: 
                $name: the second name
            my_algos: 
                - $name: the second name
        """,
    )


def test_each_skip():
    assert_config_equal(
        source="""
        hyperparameters:
            forecaster_name: dummy
            $each:
                - $None
                - epochs: 150
                  batch_size: 64
        """,
        expected="""
        - hyperparameters:
            forecaster_name: dummy
        - hyperparameters:
            forecaster_name: dummy
            epochs: 150
            batch_size: 64""",
    )


def test_each_dict():
    assert_config_equal(
        source="""
        foo:
            $each: 
                -
                    x: y
        """,
        expected="""
        - 
            foo:
                x: y
        """,
    )


def test_each_dict_overwrite():
    with pytest.raises(TypeError):
        assert_config_equal(
            source="""
            foo:
                a: b
                $each: [1, 2]
            
            """,
            expected="",
        )


def test_each_list_merge():
    assert_config_equal(
        source="""
        foo:
            - 1
            - $each:
                - 2
                - 3
        """,
        expected="""
        - foo: [1, 2]
        - foo: [1, 3]
        """,
    )


def test_each_in_list():
    assert_config_equal(
        source="""
        foo:
            - $each:
                - 1
                - 2
                - 3
        """,
        expected="""
        - foo: [1]
        - foo: [2]
        - foo: [3]
        """,
    )


def test_eval():
    assert_config_equal(
        source="""
        base:
            $eval: max(10,2)
        """,
        expected="""
        - base: 10
        """,
    )


def test_eval_in_list():
    assert_config_equal(
        source="""
        base:
            - $eval: 10
        """,
        expected="""
        - base:
            - 10
        """,
    )


def test_eval_with_trial():
    assert_config_equal(
        source="""
    a: 1
    b: 
        $eval: $.a * $trial.dataset.meta.prediction_length
    """,
        expected="""
        - 
            a: 1
            b:
                $eval: 1 * __trial__.dataset.meta.prediction_length
    """,
    )


def test_eval_algorithm_dataset_dependency():
    assert_config_equal(
        source="""
        dataset:
            meta:
                prediction_length: 1
        algorithm:
            hyperparameters:
                prediction_length:
                    $eval: $.dataset.meta.prediction_length
                context_length:
                    $eval: 2 * $.algorithm.hyperparameters.prediction_length
        """,
        expected="""
        - dataset:
            meta:
                prediction_length: 1
          algorithm:
            hyperparameters:
                prediction_length: 1
                context_length: 2
        """,
    )


def test_eval_in_each():
    assert_config_equal(
        source="""
        dataset:
            meta:
                prediction_length: 10
        base:
            hyperparameters:
                prediction_length:
                    $each:
                        - 5
                        - $eval: dataset.meta.prediction_length
        """,
        expected="""
        - dataset:
            meta:
                prediction_length: 10
          base:
            hyperparameters:
                prediction_length: 5
        - dataset:
            meta:
                prediction_length: 10
          base:
            hyperparameters:
                prediction_length: 10
        """,
    )


def test_eval_in_recursive():
    assert_config_equal(
        source="""
        a: 1
        b: 
            $eval: 2*$.a
        c:
            $eval: 1 + $.b
        """,
        expected="""
        - 
            a: 1
            b: 2
            c: 3
        """,
    )


def test_eval_indexing():
    assert_config_equal(
        source="""
        a: 
            b:
                - c: 
                    d: e
        f: 
            $eval: $.a.b[0]["c"]['d']
        """,
        expected="""
        -
            a: 
                b:
                    - c: 
                        d: e
            f: e
        """,
    )


def test_eval_indexing_recursive():
    assert_config_equal(
        source="""
        a: 
            b:
                - c: 
                    d: 
                        $eval: $.a.e["f"][0]
            e:
                f:
                    - 
                        10
        f: 
            $eval: $.a.b[0]["c"]['d']
        """,
        expected="""
        -
            a: 
                b:
                    - c: 
                        d: 10
                e:
                    f:
                        - 10
            f: 10
        """,
    )


def test_simple_example():
    assert_config_equal(**load("simple_example"))


def test_large_example():
    assert_config_equal(**load("large_example"))


def test_complex_example():
    assert_config_equal(**load("complex_example"))
