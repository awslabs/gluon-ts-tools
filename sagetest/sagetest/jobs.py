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
    metrics: dict = {}
    training_time: Optional[int]  # stopped jobs can have no training time
    hyperparameters: dict = {}
    tags: dict = {}
    source: dict = {}
    name: str

    def __getitem__(self, key: Any) -> Any:
        return self.json[key]

    def __repr__(self) -> str:
        return yaml.dump(self.json)

    def __eq__(self, other):
        return isinstance(other, Job) and self.source == other.source

    @classmethod
    def from_json(cls, sagemaker_trainingjob: dict) -> "Job":
        return cls(
            training_time=sagemaker_trainingjob.get("TrainingTimeInSeconds"),
            hyperparameters=sagemaker_trainingjob.get("HyperParameters", {}),
            tags={
                tag["Key"]: tag["Value"]
                for tag in sagemaker_trainingjob.get("Tags", {})
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


class Jobs:
    def __init__(self, job_list: List[Job] = []) -> None:
        self.data = job_list
        self.update_metrics_dataframe()

    def pop(self, index) -> Job:
        popped = self.data.pop(index)
        self.update_metrics_dataframe()
        return popped

    def update_metrics_dataframe(self) -> None:
        self.metrics = pd.DataFrame(job.metrics for job in self.data)

    def where(self, func: Callable) -> "Jobs":
        """Extract jobs where `func` evaluates to True"""
        return Jobs(list(filter(func, self.data)))

    def all(self, func: Callable) -> any:
        """Test if func evaluates to True for all jobs."""
        return all(map(func, self.data))

    def __eq__(self, other):
        return isinstance(other, Jobs) and self.data == other.data

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, key) -> Union[Job, "Jobs"]:
        if isinstance(key, slice):
            return Jobs(self.data[key])
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    @classmethod
    def from_json_list(cls, sm_jsons: List[dict]) -> "Jobs":
        return cls(list(map(Job.from_json, sm_jsons)))
