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

from datetime import datetime
from typing import List

from pydantic import BaseModel

from .jobs import Jobs


class Filter(BaseModel):
    algorithm: str = None
    image: str = None
    hyperparameters: dict = None
    dataset: str = None
    tags: dict = None
    start_time: datetime = None
    end_time: datetime = None
    names: list = None
    status: list = None
    search_filters: List[dict] = []
    max_results: int = 100

    def convert_to_sagemaker(self):
        sm_filters = []

        def add_filter(name, value, operator="Equals"):
            sm_filters.append(
                {"Name": name, "Operator": operator, "Value": str(value)}
            )

        def convert_time(time: datetime):
            return time.strftime("%Y-%m-%dT%H:%M:%SZ")

        if self.tags:
            for key, val in self.tags.items():
                add_filter(f"Tags.{key}", val)

        if self.hyperparameters:
            for key, val in self.hyperparameters.items():
                add_filter(f"HyperParameters.{key}", val)

        if self.algorithm:
            add_filter("AlgorithmSpecification.AlgorithmName", self.algorithm)

        if self.image:
            add_filter("AlgorithmSpecification.TrainingImage", self.image)

        if self.dataset:
            add_filter(
                "InputDataConfig.DataSource.S3DataSource.S3Uri", self.dataset
            )

        if self.names:
            add_filter("TrainingJobName", ",".join(self.names), operator="In")

        if self.status:
            add_filter(
                "TrainingJobStatus", ",".join(self.status), operator="In"
            )

        if self.start_time:
            add_filter("TrainingStartTime", convert_time(self.start_time))

        if self.end_time:
            add_filter("TrainingEndTime", convert_time(self.end_time))

        return sm_filters + self.search_filters


def query(job_filter: Filter, session):
    filters = job_filter.convert_to_sagemaker()
    if not filters:
        raise ValueError("Empty filters in query")

    print("querying sagemaker with these filters:\n", filters)

    sagemaker = session.client(service_name="sagemaker")
    paginator = sagemaker.get_paginator("search")

    pages = paginator.paginate(
        Resource="TrainingJob",
        SearchExpression={"Filters": filters},
        PaginationConfig={
            "PageSize": min(job_filter.max_results, 100),
            "MaxItems": job_filter.max_results,
        },
        SortBy="CreationTime",
    )

    pages = list(pages)

    # Iterate over the fetched training jobs and only save those within
    # within the desired timeframe
    all_jobs = [
        job["TrainingJob"] for page in pages for job in page["Results"]
    ]

    return Jobs.from_json_list(all_jobs)
