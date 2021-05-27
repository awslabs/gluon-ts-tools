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
from typing import List, Optional

from pydantic import BaseModel

from .jobs import Jobs


class Filter(BaseModel):
    algorithm: Optional[str]
    image: Optional[str]
    hyperparameters: Optional[dict]
    dataset: Optional[str]
    tags: Optional[dict]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    names: Optional[list]
    status: Optional[list]
    search_filters: List[dict] = []
    max_results: int = 100

    def convert_to_sagemaker(self):
        filters = []

        def op(name, value, operator="Equals"):
            return {"Name": name, "Operator": operator, "Value": str(value)}

        def convert_time(time: datetime):
            return time.strftime("%Y-%m-%dT%H:%M:%SZ")

        if self.tags:
            for key, val in self.tags.items():
                filters.append(op(f"Tags.{key}", val))

        if self.hyperparameters:
            for key, val in self.hyperparameters.items():
                filters.append(op(f"HyperParameters.{key}", val))

        if self.algorithm:
            filters.append(
                op("AlgorithmSpecification.AlgorithmName", self.algorithm)
            )

        if self.image:
            filters.append(
                op("AlgorithmSpecification.TrainingImage", self.image)
            )

        if self.dataset:
            filters.append(
                op(
                    "InputDataConfig.DataSource.S3DataSource.S3Uri",
                    self.dataset,
                )
            )

        if self.names:
            filters.append(
                op("TrainingJobName", ",".join(self.names), operator="In")
            )

        if self.status:
            filters.append(
                op("TrainingJobStatus", ",".join(self.status), operator="In")
            )

        if self.start_time:
            filters.append(
                op("TrainingStartTime", convert_time(self.start_time))
            )

        if self.end_time:
            filters.append(op("TrainingEndTime", convert_time(self.end_time)))

        return filters + self.search_filters


def query(job_filter: Filter, session):
    filters = job_filter.convert_to_sagemaker()
    if not filters:
        raise ValueError("Empty filters in query")

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
    return Jobs.from_job_descriptions(
        [job["TrainingJob"] for page in pages for job in page["Results"]]
    )
