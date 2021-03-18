import time
from typing import Dict, Iterable, List
import botocore
from toolz.itertoolz import groupby
from itertools import count


class JobDispatcher:
    """The JobDispatcher class starts training jobs in SageMaker."""

    def __init__(self, sagemaker: botocore.client):
        self.sagemaker = sagemaker

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

    def group_by_instance_type(self, jobs: Iterable[dict]) -> List[Iterable]:
        """
        This method groups all the jobs into different queues depending
        on which instance each job should be run.
        This returns a list of the different queues.

        >>> result =group_by_instance_type(
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
                lambda job: job["ResourceConfig"]["InstanceType"], jobs
            ).values()
        )

    def start_training_job(self, job: dict, max_retries: int) -> dict:
        """
        Start a training job in SageMaker, if throttled, sleep before trying again.

        Returns the response from SageMaker or `{}` if no resources remain.
        """
        for attempt in count(start=1):
            try:
                response = self.sagemaker.create_training_job(**job)
                return response
            except botocore.exceptions.ClientError as error:
                if error.response["Error"]["Code"] == "ResourceLimitExceeded":
                    return {}
                elif (
                    error.response["Error"]["Code"] == "ThrottlingException"
                    and attempt < max_retries
                ):
                    # exponential backoff as recommended by AWS
                    self.timeout_with_printer(
                        2 ** attempt, "API call limit exceeded, Sleeping..."
                    )
                else:
                    raise

    def dispatch(
        self, jobs: List[dict], max_retries: int = 10
    ) -> Dict[str, str]:
        """
        Schedules and starts training jobs in sagemaker.

        Each item in `jobs` must be valid arguments to the
        `create_training_job` method of `boto3.sagemaker.client`:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html#SageMaker.Client.create_training_job

        Each job in jobs are sorted into queues based on the instance they run on.
        `create_training_job` is then called for each item in a queue
        until no more instances are available in sagemaker. This then repeats
        for another queue until all queues are empty. If all resources are busy
        for all queues, the dispatcher sleeps until resources are available.
        """
        queues = self.group_by_instance_type(jobs)
        num_remaining = len(jobs)
        responses = {}

        # overwrites the current line in the terminal
        # \033[K deletes the remaining characters of the line
        log = lambda message, end="\r": print(
            f"\033[K{len(jobs)-num_remaining}/{len(jobs)} jobs submitted, {message}",
            end=end,
        )

        print(f"total jobs to run: {num_remaining}")
        while num_remaining:
            for queue in queues:
                while queue:
                    run = queue.pop()
                    log("submitting job: {}".format(run["TrainingJobName"]))
                    response = self.start_training_job(run, max_retries)

                    if response:
                        responses[run["TrainingJobName"]] = response
                        num_remaining -= 1
                    else:
                        queue.append(run)
                        break

            if num_remaining:
                self.timeout_with_printer(
                    60,
                    (
                        f"\r{len(jobs) - num_remaining}/{len(jobs)} jobs submitted."
                        " Instance limit reached, pausing for 60 seconds"
                    ),
                )
        log("Done!", "\n")
        return responses
