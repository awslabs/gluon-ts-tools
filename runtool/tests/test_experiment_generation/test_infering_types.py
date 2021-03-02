from runtool.datatypes import Dataset, Algorithm, Algorithms, Datasets
import yaml
from typing import Union
from runtool.runtool import infer_type

ALGORITHM = {
    "image": "012345678901.dkr.ecr.eu-west-1.amazonaws.com/gluonts/cpu:latest",
    "instance": "ml.m5.xlarge",
    "hyperparameters": {
        "prediction_length": 7,
        "freq": "D",
    },
}

DATASET = {
    "path": {
        "train": "s3://gluonts-run-tool/gluon_ts_datasets/constant/train/data.json",
        "test": "s3://gluonts-run-tool/gluon_ts_datasets/constant/test/data.json",
    }
}


def compare(data: str, expected):
    assert infer_type(data) == expected


def test_dataset():
    compare(
        data={"my_ds": DATASET},
        expected={"my_ds": Dataset(DATASET)},
    )


def test_algorithm():
    compare(
        data={"my_algo": ALGORITHM},
        expected={"my_algo": Algorithm(ALGORITHM)},
    )


def test_algorithms():
    compare(
        data={"algorithms": [ALGORITHM]},
        expected={"algorithms": Algorithms([Algorithm(ALGORITHM)])},
    )


def test_datasets():
    compare(
        data={"datasets": [DATASET]},
        expected={"datasets": Datasets([Dataset(DATASET)])},
    )
