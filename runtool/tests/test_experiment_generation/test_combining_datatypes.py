import pytest
from runtool.datatypes import (
    Algorithm,
    Algorithms,
    Dataset,
    Datasets,
    Experiment,
    Experiments,
)

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


def perform_typeerror_test(data, to_multiply):
    for item in to_multiply:
        with pytest.raises(TypeError):
            data * item
        with pytest.raises(TypeError):
            item * data


def test_algorithm_mul_algorithm():
    perform_typeerror_test(ALGORITHM, (ALGORITHM, ALGORITHMS(2)))


def test_algorithms_mul_algorithms():
    perform_typeerror_test(ALGORITHMS(2), (ALGORITHMS(2)))


def test_dataset_mul_dataset():
    perform_typeerror_test(DATASET, (DATASET, DATASETS(2)))


def test_datasets_mul_datasets():
    perform_typeerror_test(DATASETS(2), (DATASETS(2)))


def test_algorithm_mul_dataset():
    assert ALGORITHM * DATASET == EXPERIMENTS(1)
    assert DATASET * ALGORITHM == EXPERIMENTS(1)


def test_algorithm_mul_datasets():
    assert ALGORITHM * DATASETS(2) == EXPERIMENTS(2)
    assert DATASETS(2) * ALGORITHM == EXPERIMENTS(2)


def test_algorithms_mul_dataset():
    assert ALGORITHMS(2) * DATASET == EXPERIMENTS(2)
    assert DATASET * ALGORITHMS(2) == EXPERIMENTS(2)


def test_algorithms_mul_datasets():
    assert DATASETS(2) * ALGORITHMS(2) == EXPERIMENTS(4)
    assert ALGORITHMS(2) * DATASETS(2) == EXPERIMENTS(4)


def test_algorithm_plus_algorithm():
    assert ALGORITHM + ALGORITHM == ALGORITHMS(2)


def test_algorithm_plus_algorithms():
    assert ALGORITHM + ALGORITHMS(2) == ALGORITHMS(3)
    assert ALGORITHMS(2) + ALGORITHM == ALGORITHMS(3)


def test_algorithm_plus_dataset():
    with pytest.raises(TypeError):
        ALGORITHM + DATASET
        DATASET + ALGORITHM


def test_algorithms_plus_dataset():
    with pytest.raises(TypeError):
        ALGORITHMS(1) + DATASET
        DATASET + ALGORITHMS(1)


def test_datasets_plus_algorithm():
    with pytest.raises(TypeError):
        DATASETS(1) + ALGORITHM
        ALGORITHM + DATASETS(1)


def test_datasets_plus_algorithms():
    with pytest.raises(TypeError):
        DATASETS(1) + ALGORITHMS(1)
        ALGORITHMS(1) + DATASETS(1)


def test_experiment_plus_experiment():
    assert EXPERIMENT + EXPERIMENT == EXPERIMENTS(2)


def test_experiment_plus_experiments():
    assert EXPERIMENT + EXPERIMENTS(2) == EXPERIMENTS(3)
    assert EXPERIMENTS(2) + EXPERIMENT == EXPERIMENTS(3)


def test_experiments_plus_experiments():
    assert EXPERIMENTS(2) + EXPERIMENTS(2) == EXPERIMENTS(4)


def test_experiment_mul():
    perform_typeerror_test(
        EXPERIMENT,
        (
            ALGORITHM,
            ALGORITHMS(2),
            DATASET,
            DATASETS(2),
            EXPERIMENT,
            EXPERIMENTS(2),
        ),
    )


def test_experiments_mul():
    perform_typeerror_test(
        EXPERIMENTS(2),
        (
            ALGORITHM,
            ALGORITHMS(2),
            DATASET,
            DATASETS(2),
            EXPERIMENT,
            EXPERIMENTS(2),
        ),
    )
