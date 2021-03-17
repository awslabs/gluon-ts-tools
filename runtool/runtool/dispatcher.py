import time
from typing import Dict, Iterable, List
import botocore
from toolz.itertoolz import groupby


class JobsDispatcher:
    """
    The JobsDispatcher class starts training jobs in SageMaker.
    """

    def __init__(self, client: botocore.client):
        self.client = client

    def timeout_with_printer(self, timeout, message="") -> None:
        """
        Prints a message with a countdown over and over on the same row.
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
        Tries to start a single training jobs on SageMaker.
        Returns the response from SageMaker or, if no more instances
        are available,returns an empty response.
        If throttled, this method sleeps before trying again.
        """
        retries = 0
        while True:
            try:
                response = self.client.create_training_job(**job)
                time.sleep(4)  # wait to avoid throttling
                return response
            except botocore.exceptions.ClientError as error:
                if error.response["Error"]["Code"] == "ResourceLimitExceeded":
                    return {}
                if (
                    error.response["Error"]["Code"] == "ThrottlingException"
                    and retries < max_retries
                ):
                    # exponential backoff as recommended by AWS
                    self.timeout_with_printer(
                        60 + 2 ** retries,
                        "API call limit exceeded, Sleeping...",
                    )
                    retries += 1
                else:
                    raise error

    def dispatch(
        self, jobs: List[dict], max_retries: int = 10
    ) -> Dict[str, str]:
        """
        This method uses the dictionaries in the `jobs` parameter
        to dispatch training jobs to SageMaker using boto3.
        Each of the dictionaries must be valid arguments to the
        create_training_job method of boto3 which is detailed here:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html#SageMaker.Client.create_training_job

        The passed dictionaries are sorted into different queues
        based on the instance the jobs should be run on.
        Thereafter, jobs are dispatched from one of the queues while
        instances are available on the AWS account.
        When a 'ResourceLimitExceeded' exception is raised, this is repeated
        for another queue until all jobs are dispatched.
        If at any point, all resources are busy the dispatcher waits
        for resources to become available.
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
