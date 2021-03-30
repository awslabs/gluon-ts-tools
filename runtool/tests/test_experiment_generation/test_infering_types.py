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
