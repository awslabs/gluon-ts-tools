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

from typing import Any, Callable, List, Optional, Union

import pandas as pd
import yaml
from pydantic import BaseModel


class Job(BaseModel):
    """
    The Job class represents a single SageMaker training job.

    The job description which SageMaker uses to describe training jobs is
    a very verbose JSON. This complicates writing tests on these jobs. The
    `Job` class is a thin wrapper around the SageMaker job description which
    makes common features such as the training job name or tags easily
    accessible.

    The `Job` class is used to represent individual training jobs within the
    `Jobs` class.
    """

    metrics: dict = {}
    training_time: Optional[int]  # stopped jobs can have no training time
    hyperparameters: dict = {}
    tags: dict = {}
    source: dict = {}
    name: str

    @classmethod
    def from_job_description(cls, sagemaker_trainingjob: dict) -> "Job":
        """
        Convert a TrainingJob response from the SageMaker Search api into
        a `Job` object.

        An valid value of the sagemaker_trainingjob parameter should follow
        this specification:
        https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_TrainingJob.html
        """
        return cls(
            training_time=sagemaker_trainingjob.get("TrainingTimeInSeconds"),
            hyperparameters=sagemaker_trainingjob.get("HyperParameters", {}),
            tags={
                tag["Key"]: tag["Value"]
                for tag in sagemaker_trainingjob.get("Tags", [])
            },
            metrics={
                metric["MetricName"]: metric["Value"]
                for metric in sagemaker_trainingjob.get(
                    "FinalMetricDataList", []
                )
            },
            source=sagemaker_trainingjob,
            name=sagemaker_trainingjob["TrainingJobName"],
        )

    def __getitem__(self, key: Any) -> Any:
        return self.source[key]

    def __repr__(self) -> str:
        return yaml.dump(self.source)


class Jobs:
    """
    The `Jobs` class simplifies testing on groups of SageMaker training jobs.

    For example, a `Jobs` object has a `metrics` attribute which makes it
    easy to test aggregate metrics for several training jobs.

    >>> jobs = Jobs(
    ...     [
    ...         Job(name="job1", training_time=60, metrics={"MSE": 10}),
    ...         Job(name="job2", training_time=80, metrics={"MSE": 2}),
    ...     ]
    ... )
    >>> jobs.metrics["MSE"].mean()
    6

    One can also filter out a subset of jobs using the `where` method:

    >>> jobs.where(lamdba job: job.metrics["MSE"] == 2) == Jobs(
            [Job(name="job2", training_time=80, metrics={"MSE": 2})]
        )
    True

    Or if one wishes to apply a test to all individual jobs in a `Jobs` object
    this can be done via the `all` method.

    >>> jobs.all(lambda job: job.training_time < 100)
    True
    """

    def __init__(self, jobs: List[Job]) -> None:
        self.jobs = jobs
        self.update_metrics_dataframe()

    @classmethod
    def from_job_descriptions(
        cls, sagemaker_trainingjobs: List[dict]
    ) -> "Jobs":
        """
        Create a `Jobs` object from a list of SageMaker TrainingJob JSON.

        Each item in the `sagemaker_trainingjobs` parameter must adhere to the
        below specification.
        https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_TrainingJob.html\
        """
        return cls(list(map(Job.from_job_description, sagemaker_trainingjobs)))

    def pop(self, index) -> Job:
        value = self.jobs.pop(index)
        self.update_metrics_dataframe()
        return value

    def update_metrics_dataframe(self) -> None:
        self.metrics = pd.DataFrame(job.metrics for job in self.jobs)

    def where(self, func: Callable) -> "Jobs":
        """Extract jobs where `func` evaluates to True"""
        return Jobs(list(filter(func, self.jobs)))

    def all(self, func: Callable) -> any:
        """Test if func evaluates to True for all jobs."""
        return all(map(func, self.jobs))

    def __eq__(self, other):
        return isinstance(other, Jobs) and self.jobs == other.jobs

    def __len__(self) -> int:
        return len(self.jobs)

    def __getitem__(self, key) -> Union[Job, "Jobs"]:
        if isinstance(key, slice):
            return Jobs(self.jobs[key])
        return self.jobs[key]

    def __iter__(self):
        return iter(self.jobs)
