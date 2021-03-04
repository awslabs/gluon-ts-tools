import sys
import time
from typing import Dict, Iterable, List

import boto3
import botocore


class JobsDispatcher:
    """
    The JobsDispatcher class interfaces with SageMaker in order
    to dispatch training jobs.
    """

    def __init__(self, session: boto3.Session):
        self.client = session.client("sagemaker")

    def timeout_with_printer(self, timeout, message="") -> None:
        """
        Prints a message with a countdown over and over on the same row.
        This method waits one second between prints.
        """
        for remaining in range(timeout, 0, -1):
            sys.stdout.write(
                "\r{}, {:2d} seconds remaining.".format(message, remaining)
            )
            sys.stdout.flush()
            time.sleep(1)

        sys.stdout.write("\r")
        sys.stdout.flush()

    def group_by_instance_type(_, jobs: Iterable[dict]) -> List[Iterable]:
        """
        This method sorts all the jobs into different queues depending
        on which instance each job should be run.
        This returns a list of the different queues.
        """
        instance_queues = {}
        for job in jobs:
            instance_type = job["ResourceConfig"]["InstanceType"]
            if instance_type in instance_queues:
                instance_queues[instance_type].append(job)
            else:
                instance_queues[instance_type] = [job]
        return list(instance_queues.values())

    def dispatch(self, runs: Iterable[dict]) -> Dict[str, str]:
        """
        This method uses the dictionaries in the `runs` parameter
        to dispatch training jobs to SageMaker using boto3.
        Each of the dictionaries must be valid arguments to the
        create_training_job method of boto3 which is detailed here:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sagemaker.html#SageMaker.Client.create_training_job

        The passed dictionaries will be sorted into different queues
        based on the instance the jobs should be run on.
        Thereafter, jobs are dispatched from one of the queues while
        instances are available on the AWS account.
        When a 'ResourceLimitExceeded' exception is raised, this is repeated
        for another queue until all jobs are dispatched.
        If at any point, all resources are busy the dispatcher waits
        for resources to become available.
        """
        runs = list(runs)
        queues = self.group_by_instance_type(runs)
        remaining_jobs = len(runs)
        responses = {}
        retries = 0  # used for exponential backoff if throttled

        # overwrites the current line in the terminal
        # \033[K deletes the remaining characters of the line
        log = lambda message: print(
            f"\033[K{len(runs)-remaining_jobs}/{len(runs)} jobs submitted, {message}",
            end="\r",
        )

        print(f"total jobs to run: {remaining_jobs}")
        while remaining_jobs:
            for queue in queues:
                # 1. run as many jobs as possible for the given queue
                while queue:
                    run = queue.pop()
                    log("submitting job: {}".format(run["TrainingJobName"]))
                    try:
                        responses[
                            run["TrainingJobName"]
                        ] = self.client.create_training_job(**run)
                        remaining_jobs -= 1
                        time.sleep(4)
                    except self.client.exceptions.ResourceLimitExceeded:
                        # all resources busy,
                        queue.append(run)
                        break
                    except botocore.exceptions.ValidationError as e:
                        print(
                            "an error occured, likely due to invalid instance type being choosen\n",
                            "you should stop any started jobs in sagemaker, fix the issue and rerun this program\n",
                            "the error was:",
                            e,
                        )
                        return False
                    except botocore.exceptions.ClientError as error:
                        queue.append(run)
                        if (
                            error.response["Error"]["Code"]
                            == "ThrottlingException"
                        ):
                            log("API call limit exceeded; Sleeping...\033[K")
                            # exponential backoff as recommended by AWS
                            # minimum wait is 10 minutes
                            retries += 1
                            self.timeout_with_printer(10 * 60 + 10 ** retries)
                        else:
                            raise Exception(f"Unknown error occurred: {error}")

            if remaining_jobs:
                self.timeout_with_printer(
                    60,
                    (
                        f"\r{len(runs) - remaining_jobs}/{len(runs)} jobs submitted."
                        " Instance limit reached, pausing for 60 seconds"
                    ),
                )
        log("Done!")
        return responses
