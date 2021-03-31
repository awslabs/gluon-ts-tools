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

import pytest
from runtool.datatypes import (
    Algorithm,
    Algorithms,
    Dataset,
    Datasets,
    Experiment,
    Experiments,
)
from runtool.recurse_config import Versions

ALGORITHM = Algorithm(
    {
        "image": "012345678901.dkr.ecr.eu-west-1.amazonaws.com/gluonts/cpu:latest",
        "instance": "ml.m5.xlarge",
        "hyperparameters": {
            "prediction_length": 7,
            "freq": "D",
        },
    }
)

DATASET = Dataset(
    {
        "path": {
            "train": "s3://gluonts-run-tool/gluon_ts_datasets/constant/train/data.json",
            "test": "s3://gluonts-run-tool/gluon_ts_datasets/constant/test/data.json",
        }
    }
)

EXPERIMENT = Experiment.from_nodes(ALGORITHM, DATASET)
ALGORITHMS = lambda num: Algorithms([ALGORITHM] * num)
DATASETS = lambda num: Datasets([DATASET] * num)
EXPERIMENTS = lambda num: Experiments([EXPERIMENT] * num)
VERSIONS = lambda item, num: Versions([item] * num)


def perform_typeerror_test(data, to_multiply):
    for item in to_multiply:
        with pytest.raises(TypeError):
            data * item
        with pytest.raises(TypeError):
            item * data


def test_versions_algorithm_mul_versions_dataset():
    assert VERSIONS(ALGORITHM, 1) * VERSIONS(DATASET, 1) == EXPERIMENTS(1)
    assert VERSIONS(DATASET, 1) * VERSIONS(ALGORITHM, 1) == EXPERIMENTS(1)


def test_versions_algorithm_mul_versions_datasets():
    assert VERSIONS(ALGORITHM, 1) * VERSIONS(DATASETS(4), 1) == EXPERIMENTS(4)
    assert VERSIONS(DATASETS(4), 1) * VERSIONS(ALGORITHM, 1) == EXPERIMENTS(4)


def test_versions_algorithms_mul_versions_dataset():
    assert VERSIONS(ALGORITHMS(4), 1) * VERSIONS(DATASET, 1) == EXPERIMENTS(4)
    assert VERSIONS(DATASET, 1) * VERSIONS(ALGORITHMS(4), 1) == EXPERIMENTS(4)


def test_versions_algorithms_mul_versions_datasets():
    assert VERSIONS(ALGORITHMS(4), 1) * VERSIONS(
        DATASETS(4), 1
    ) == EXPERIMENTS(16)
    assert VERSIONS(DATASETS(4), 1) * VERSIONS(
        ALGORITHMS(4), 1
    ) == EXPERIMENTS(16)


def test_versions_int_mul_versions_datasets():
    perform_typeerror_test(VERSIONS(DATASET, 1), VERSIONS(1, 3))


def test_versions_str_mul_versions_datasets():
    perform_typeerror_test(VERSIONS(DATASET, 1), VERSIONS("hello", 3))
