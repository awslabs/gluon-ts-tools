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

import time
from itertools import count
from typing import Dict, Iterable, List, NamedTuple, NewType, Optional

import boto3
import botocore
from toolz.itertoolz import groupby

JobConfiguration = NewType("JobConfiguration", dict)


def group_by_instance_type(
    jobs: Iterable[JobConfiguration],
) -> List[List[JobConfiguration]]:
    """
    Group job-configuration into different queues depending on which instance
    each job should be run. This returns a list of the different queues.

    >>> result = group_by_instance_type(
    ...     [
    ...         {"ResourceConfig": {"InstanceType": 1}, "name": 1},
    ...         {"ResourceConfig": {"InstanceType": 2}, "name": 2},
    ...         {"ResourceConfig": {"InstanceType": 2}, "name": 3},
    ...     ]
    ... )
    >>> result == [
    ...     [
    ...         {"ResourceConfig": {"InstanceType": 1}, "name": 1}
    ...     ],
    ...     [
    ...         {"ResourceConfig": {"InstanceType": 2}, "name": 2},
    ...         {"ResourceConfig": {"InstanceType": 2}, "name": 3},
    ...     ],
    ... ]
    True
    """
    return list(
        groupby(
            lambda job_config: job_config["ResourceConfig"]["InstanceType"],
            jobs,
        ).values()
    )


class JobDispatcher(NamedTuple):
    """The JobDispatcher starts training jobs in SageMaker."""

    sagemaker: boto3.client

    def timeout_with_printer(self, timeout, message="") -> None:
        """
        Print a message with a countdown over and over on the same row.
        This method waits one second between prints.
        """
        for remaining in range(timeout, 0, -1):
            print(
                f"\r\033[K{message}, {remaining:2d} seconds remaining.", end=""
            )
            time.sleep(1)

        print("\r", end="")

    def start_training_job(
        self, job: JobConfiguration, max_retries: int
    ) -> Optional[dict]:
        """
        Start a training job in SageMaker, if throttled, sleep and try again.

        Returns the response from SageMaker or `None` if no resources remain.
        Returning `None` instead of waiting for the resources to be released
        allows the caller to the `start_training_job` to start other jobs on
        other instance types instead of waiting for resources to be freed.
        This improves parallelism and can greatly improve speedup depending on
        which instance types are used.
        """
        for attempt in count(start=1):
            try:
                return self.sagemaker.create_training_job(**job)
            except botocore.exceptions.ClientError as error:
                failure_reason = error.response["Error"]["Code"]

                if failure_reason == "ResourceLimitExceeded":
                    return None

                if (
                    failure_reason == "ThrottlingException"
                    and attempt < max_retries
                ):
                    # exponential backoff as recommended by AWS
                    self.timeout_with_printer(
                        2 ** attempt, "API call limit exceeded, Sleeping..."
                    )
                else:
                    raise

    def dispatch(
        self, jobs: List[JobConfiguration], max_retries: int = 10
    ) -> Dict[str, str]:
        """
        Schedule and start training jobs in sagemaker.

        Each item in `jobs` must be valid arguments to the
        `create_training_job` method of `boto3.sagemaker.client`:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html#SageMaker.Client.create_training_job

        Each job in jobs are sorted into queues based on the instance they run
        on.`create_training_job` is then called for each item in a queue until
        no more instances are available in sagemaker. This then repeats for
        another queue until all queues are empty. If all resources are busy
        for all queues, the dispatcher sleeps until resources are available.
        """
        queues = group_by_instance_type(jobs)
        responses = {}

        def log(message, end="\r"):
            """Overwrite previous line in the terminal with `message`"""
            # \033[K deletes the remaining characters of the line
            print(
                f"\033[K{len(responses)}/{len(jobs)} jobs submitted, {message}",
                end=end,
            )

        print(f"total jobs to run: {len(jobs)}")
        while True:
            for queue in queues:
                while queue:
                    run = queue.pop()
                    log(f"submitting job: {run['TrainingJobName']}")
                    response = self.start_training_job(run, max_retries)

                    if response:
                        responses[run["TrainingJobName"]] = response
                    else:
                        queue.append(run)
                        break

            if any(queues):
                self.timeout_with_printer(
                    60,
                    (
                        f"\r{len(responses)}/{len(jobs)} jobs submitted."
                        " Instance limit reached, pausing for 60 seconds"
                    ),
                )
            else:
                break
        log("Done!", "\n")
        return responses
