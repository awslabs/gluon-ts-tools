import runtool
import yaml
from runtool import expand_experiments
from runtool.datatypes import *
from runtool.utils import recurse_print
from typing import Union


def get_config(source: str) -> Union[list, dict]:
    return runtool.load_config(yaml.safe_load(source))


def compare(
    source: str,
    expected: Union[list, dict],
    expression: str = "conf.algorithms * conf.datasets",
) -> None:
    conf = get_config(source)
    experiments = [
        run.to_base() for run in expand_experiments(eval(expression))
    ]

    assert experiments == expected


def test_trial_eval_nested():
    compare(
        """
        algorithms:
            -  
                $type: Algorithm
                image: an/image/path
                instance: ml.m5.large
                hyperparameters:
                    hps_1: 1
                    prediction_length: 
                        $eval: 2 * $trial.dataset.meta.prediction_length
        datasets:
            -  
                $type: Dataset
                meta:
                    prediction_length:
                        $eval: 1 + $trial.algorithm.hyperparameters.hps_1
                path:
                    train: a/path
                    test: test/path
        """,
        [
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.large",
                    "hyperparameters": {"hps_1": 1, "prediction_length": 4},
                },
                "dataset": {
                    "$type": "Dataset",
                    "meta": {"prediction_length": 2},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            }
        ],
    )


def test_trial_eval_in_each():
    compare(
        """
    a: 2
    algo:
        $type: Algorithm
        image: an/image/path
        instance: 
            $each:
                - ml.m5.large
                - ml.m5.2xlarge
        hyperparameters:
            prediction_length: 
                $eval: $.a * $trial.dataset.meta.prediction_length
    ds:  
        $type: Dataset
        meta:
            prediction_length: 7
        path:
            train: a/path
            test: test/path
    algorithms:
        - $ref: algo
    datasets:
        - $ref: ds
    """,
        [
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.large",
                    "hyperparameters": {"prediction_length": 14},
                },
                "dataset": {
                    "$type": "Dataset",
                    "meta": {"prediction_length": 7},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.2xlarge",
                    "hyperparameters": {"prediction_length": 14},
                },
                "dataset": {
                    "$type": "Dataset",
                    "meta": {"prediction_length": 7},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
        ],
    )


def test_trial_eval_n_each_plus_static_algo():
    compare(
        """
    a: 2
    algo:
        image: an/image/path
        instance: 
            $each:
                - ml.m5.large
                - ml.m5.2xlarge
        hyperparameters:
            prediction_length: 
                $eval: $.a * $trial.dataset.meta.prediction_length
    ds:
        meta:
            prediction_length: 7
        path:
            train: a/path
            test: test/path
    algorithms:
        - 
            $ref: algo
        -  
            $type: Algorithm
            image: an/image/path
            instance: ml.m5.large
            hyperparameters:
                prediction_length: 1
    datasets:
        - $ref: ds
    """,
        [
            {
                "algorithm": {
                    "image": "an/image/path",
                    "instance": "ml.m5.large",
                    "hyperparameters": {"prediction_length": 14},
                },
                "dataset": {
                    "meta": {"prediction_length": 7},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.large",
                    "hyperparameters": {"prediction_length": 1},
                },
                "dataset": {
                    "meta": {"prediction_length": 7},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
            {
                "algorithm": {
                    "image": "an/image/path",
                    "instance": "ml.m5.2xlarge",
                    "hyperparameters": {"prediction_length": 14},
                },
                "dataset": {
                    "meta": {"prediction_length": 7},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
        ],
    )


def test_trial_ds_each():
    compare(
        """
    a: 2
    algo:
        $type: Algorithm
        image: an/image/path
        instance: ml.m5.2xlarge
        hyperparameters:
            prediction_length: 
                $eval: $.a * $trial.dataset.meta.prediction_length
    ds:  
        $type: Dataset
        meta:
            prediction_length: 
                $each:
                    - 7
                    - 14
        path:
            train: a/path
            test: test/path
    algorithms:
        - $ref: algo
    datasets:
        - $ref: ds
    """,
        [
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.2xlarge",
                    "hyperparameters": {"prediction_length": 14},
                },
                "dataset": {
                    "$type": "Dataset",
                    "meta": {"prediction_length": 7},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.2xlarge",
                    "hyperparameters": {"prediction_length": 28},
                },
                "dataset": {
                    "$type": "Dataset",
                    "meta": {"prediction_length": 14},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
        ],
    )


def test_trial_ds_each_with_static_ds():
    compare(
        """
    algo:
        image: an/image/path
        instance: ml.m5.2xlarge
        hyperparameters:
            prediction_length: 
                $eval: 2 * $trial.dataset.meta.prediction_length
    ds:
        meta:
            prediction_length: 
                $each:
                    - 7
                    - 14
        path:
            train: a/path
            test: test/path
    algorithms:
        - $ref: algo
    datasets:
        - $ref: ds
        -
            meta:
                prediction_length: 1 
            path:
                train: a/path/2
                test: test/path/2
    """,
        [
            {
                "algorithm": {
                    "image": "an/image/path",
                    "instance": "ml.m5.2xlarge",
                    "hyperparameters": {"prediction_length": 14},
                },
                "dataset": {
                    "meta": {"prediction_length": 7},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
            {
                "algorithm": {
                    "image": "an/image/path",
                    "instance": "ml.m5.2xlarge",
                    "hyperparameters": {"prediction_length": 2},
                },
                "dataset": {
                    "meta": {"prediction_length": 1},
                    "path": {"train": "a/path/2", "test": "test/path/2"},
                },
            },
            {
                "algorithm": {
                    "image": "an/image/path",
                    "instance": "ml.m5.2xlarge",
                    "hyperparameters": {"prediction_length": 28},
                },
                "dataset": {
                    "meta": {"prediction_length": 14},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
        ],
    )


def test_trial_each_in_algo_n_ds_plus_eval():
    compare(
        """
    a: 2
    algo:
        $type: Algorithm
        image: an/image/path
        instance: 
            $each:
                - ml.m5.large
                - ml.m5.2xlarge
        hyperparameters:
            prediction_length: 
                $eval: $.a * $trial.dataset.meta.prediction_length
    ds:  
        $type: Dataset
        meta:
            prediction_length: 
                $each:
                    - 7
                    - 14
        path:
            train: a/path
            test: test/path
    algorithms:
        - $ref: algo
    datasets:
        - $ref: ds
    """,
        [
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.2xlarge",
                    "hyperparameters": {"prediction_length": 28},
                },
                "dataset": {
                    "$type": "Dataset",
                    "meta": {"prediction_length": 14},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.2xlarge",
                    "hyperparameters": {"prediction_length": 14},
                },
                "dataset": {
                    "$type": "Dataset",
                    "meta": {"prediction_length": 7},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.large",
                    "hyperparameters": {"prediction_length": 28},
                },
                "dataset": {
                    "$type": "Dataset",
                    "meta": {"prediction_length": 14},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
            {
                "algorithm": {
                    "$type": "Algorithm",
                    "image": "an/image/path",
                    "instance": "ml.m5.large",
                    "hyperparameters": {"prediction_length": 14},
                },
                "dataset": {
                    "$type": "Dataset",
                    "meta": {"prediction_length": 7},
                    "path": {"train": "a/path", "test": "test/path"},
                },
            },
        ],
    )
