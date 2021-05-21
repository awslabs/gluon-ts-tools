from datetime import datetime
from typing import List, NamedTuple

import pytest
from sagetest import Filter


class SearchFilter:
    def __init__(self, name, operator, value) -> None:
        self.Name = name
        self.Operator = operator
        self.Value = value


@pytest.mark.parametrize(
    "filter,search_filters",
    [
        (
            Filter(names=["job_1"]),
            [SearchFilter("TrainingJobName", "In", "job_1")],
        ),
        (
            Filter(names=["job_1", "job_2"]),
            [SearchFilter("TrainingJobName", "In", "job_1,job_2")],
        ),
        (
            Filter(algorithm="arn:aws:some_algorithm_name"),
            [
                SearchFilter(
                    "AlgorithmSpecification.AlgorithmName",
                    "Equals",
                    "arn:aws:some_algorithm_name",
                )
            ],
        ),
        (
            Filter(image="image_url"),
            [
                SearchFilter(
                    "AlgorithmSpecification.TrainingImage",
                    "Equals",
                    "image_url",
                )
            ],
        ),
        (
            Filter(hyperparameters={"epochs": 100, "prediction_length": 24}),
            [
                SearchFilter("HyperParameters.epochs", "Equals", "100"),
                SearchFilter(
                    "HyperParameters.prediction_length", "Equals", "24"
                ),
            ],
        ),
        (
            Filter(dataset="s3://bucket/some/path"),
            [
                SearchFilter(
                    "InputDataConfig.DataSource.S3DataSource.S3Uri",
                    "Equals",
                    "s3://bucket/some/path",
                ),
            ],
        ),
        (
            Filter(tags={"my_tag_1": "value_1", "my_tag_2": "value_2"}),
            [
                SearchFilter("Tags.my_tag_1", "Equals", "value_1"),
                SearchFilter("Tags.my_tag_2", "Equals", "value_2"),
            ],
        ),
        (
            Filter(tags={"my_tag_1": "value_1"}),
            [
                SearchFilter("Tags.my_tag_1", "Equals", "value_1"),
            ],
        ),
        (
            Filter(start_time=datetime(2021, 1, 1)),
            [
                SearchFilter(
                    "TrainingStartTime", "Equals", "2021-01-01T00:00:00Z"
                ),
            ],
        ),
        (
            Filter(end_time=datetime(2021, 1, 1)),
            [
                SearchFilter(
                    "TrainingEndTime", "Equals", "2021-01-01T00:00:00Z"
                ),
            ],
        ),
        (
            Filter(status=["Completed"]),
            [
                SearchFilter("TrainingJobStatus", "In", "Completed"),
            ],
        ),
        (
            Filter(status=["Completed", "Running"]),
            [
                SearchFilter("TrainingJobStatus", "In", "Completed,Running"),
            ],
        ),
        (
            Filter(
                search_filters=[
                    {
                        "Name": "TrainingJobStatus",
                        "Operator": "In",
                        "Value": "Completed,Running",
                    }
                ]
            ),
            [
                SearchFilter("TrainingJobStatus", "In", "Completed,Running"),
            ],
        ),
    ],
)
def test_single_filters(filter: Filter, search_filters):
    assert filter.convert_to_sagemaker() == list(map(vars, search_filters))


def test_combined_filter():
    filter = Filter(
        names=["job_1"],
        algorithm="arn:aws:some_algorithm_name",
        image="image_url",
        status=["Completed", "Stopped"],
        hyperparameters={"epochs": 100, "prediction_length": 24},
        dataset="s3://bucket/some/path",
        tags={"my_tag_1": "value_1", "my_tag_2": "value_2"},
        start_time=datetime(2021, 1, 1),
        end_time=datetime(2021, 1, 1),
        search_filters=[
            {"Name": "TrainingJobStatus", "Operator": "In", "Value": "Running"}
        ],
    )
    expected = [
        ("Tags.my_tag_1", "Equals", "value_1"),
        ("Tags.my_tag_2", "Equals", "value_2"),
        ("HyperParameters.epochs", "Equals", "100"),
        ("HyperParameters.prediction_length", "Equals", "24"),
        (
            "AlgorithmSpecification.AlgorithmName",
            "Equals",
            "arn:aws:some_algorithm_name",
        ),
        ("AlgorithmSpecification.TrainingImage", "Equals", "image_url"),
        (
            "InputDataConfig.DataSource.S3DataSource.S3Uri",
            "Equals",
            "s3://bucket/some/path",
        ),
        ("TrainingJobName", "In", "job_1"),
        ("TrainingJobStatus", "In", "Completed,Stopped"),
        ("TrainingStartTime", "Equals", "2021-01-01T00:00:00Z"),
        ("TrainingEndTime", "Equals", "2021-01-01T00:00:00Z"),
        ("TrainingJobStatus", "In", "Running"),
    ]
    assert filter.convert_to_sagemaker() == [
        vars(SearchFilter(*args)) for args in expected
    ]
