from typing import Any

from runtool.datatypes import (
    Algorithm,
    Algorithms,
    Dataset,
    Datasets,
    Experiment,
    Experiments,
)
from runtool.recurse_config import Versions
from runtool.runtool import transform_config
from toolz.dicttoolz import valmap

DATASET = {
    "path": {
        "train": "s3://gluonts-run-tool/gluon_ts_datasets/constant/train/data.json",
        "test": "s3://gluonts-run-tool/gluon_ts_datasets/constant/test/data.json",
    }
}

ALGORITHM = {
    "image": "012345678901.dkr.ecr.eu-west-1.amazonaws.com/gluonts/cpu:latest",
    "instance": "ml.m5.xlarge",
    "hyperparameters": {
        "prediction_length": 7,
        "freq": "D",
    },
}

EXPERIMENT = Experiment({"algorithm": ALGORITHM, "dataset": DATASET})


def compare(source: dict, expected: Any):
    assert transform_config(source) == expected


def test_experiment_identification():
    compare(
        {"my_experiment": {"algorithm": ALGORITHM, "dataset": DATASET}},
        {"my_experiment": Versions([EXPERIMENT])},
    )


def test_experiments_identification():
    compare(
        {"my_experiments": [EXPERIMENT]},
        {"my_experiments": Versions([Experiments([EXPERIMENT])])},
    )


def test_algorithm_identification():
    compare(
        {"algorithm": ALGORITHM},
        {"algorithm": Versions([Algorithm(ALGORITHM)])},
    )


def test_algorithms_identification():
    compare(
        {"algo": [ALGORITHM]},
        {"algo": Versions([Algorithms([Algorithm(ALGORITHM)])])},
    )


def test_dataset_identification():
    compare(
        {"ds": DATASET},
        {"ds": Versions([Dataset(DATASET)])},
    )


def test_datasets_identification():
    compare(
        {"ds": [DATASET]},
        {"ds": Versions([Datasets([Dataset(DATASET)])])},
    )


def test_all_in_one():
    compare(
        {
            "dataset": DATASET,
            "datasets": [DATASET],
            "algorithm": ALGORITHM,
            "algorithms": [ALGORITHM],
            "experiment": {"algorithm": ALGORITHM, "dataset": DATASET},
            "experiments": [{"algorithm": ALGORITHM, "dataset": DATASET}],
        },
        {
            "dataset": Versions([Dataset(DATASET)]),
            "datasets": Versions([Datasets([Dataset(DATASET)])]),
            "algorithm": Versions([Algorithm(ALGORITHM)]),
            "algorithms": Versions([Algorithms([Algorithm(ALGORITHM)])]),
            "experiment": Versions([EXPERIMENT]),
            "experiments": Versions([Experiments([EXPERIMENT])]),
        },
    )
