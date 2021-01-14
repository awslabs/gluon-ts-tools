import sys
import time

import botocore
from runtool import paths


class JobsDispatcher:
    cache_path = paths.get_cache_dir()
    client = None

    def __init__(self, session):
        self.client = session.client("sagemaker")

    def timeout_with_printer(self, timeout, message=""):
        for remaining in range(timeout, 0, -1):
            sys.stdout.write("\r")
            sys.stdout.write(
                "{}, {:2d} seconds remaining.".format(message, remaining)
            )
            sys.stdout.flush()
            time.sleep(1)

        sys.stdout.write("\r")

    def write_response(self, run, response):
        with open(self.cache_path + "/jobs.json", "a") as f:
            f.write("{")
            f.write(
                '"{}":"{}"'.format(
                    run["TrainingJobName"],
                    response["TrainingJobArn"],
                )
            )
            f.write("}\n")

    def dispatch(self, runs):
        instance_queues = {}
        all_jobs = 0
        responses = {}
        for run in runs:
            all_jobs += 1
            instance_type = run["ResourceConfig"]["InstanceType"]
            if instance_type in instance_queues:
                instance_queues[instance_type].append(run)
            else:
                instance_queues[instance_type] = [run]

        jobs_to_run = all_jobs
        print(f"total jobs to run: {jobs_to_run}")
        # exponential backoff, used as 2**retries
        retries = 0
        while jobs_to_run:
            for _, queue in instance_queues.items():
                # 1. run as many jobs as possible for the given queue
                has_resources = True
                while has_resources:
                    if not queue:
                        break
                    run = queue.pop()
                    jobs_done = all_jobs - jobs_to_run
                    current_job = run["TrainingJobName"]
                    print(
                        f"\r{jobs_done}/{all_jobs} jobs submitted, submitting job: {current_job}\033[K",
                        end="",
                    )
                    try:
                        response = self.client.create_training_job(**run)
                        responses[current_job] = response
                        self.write_response(run, response)
                        jobs_to_run -= 1
                        time.sleep(4)

                    except self.client.exceptions.ResourceLimitExceeded:
                        # unable to upload more jobs for now
                        queue.append(run)
                        has_resources = False

                    except botocore.exceptions.ValidationError as e:
                        print(
                            "an error occured, likely due to invalid instance type being choosen\n",
                            "you should stop any started jobs in sagemaker, fix the issue and rerun this program\n",
                            "the error was:",
                        )
                        print(e)
                        return False
                    except botocore.exceptions.ClientError as error:
                        queue.append(run)
                        if (
                            error.response["Error"]["Code"]
                            == "ThrottlingException"
                        ):
                            print(
                                f"\r{jobs_done}/{all_jobs} jobs submitted. API call limit exceeded; backing off and retrying in a bit\033[K",
                                end="",
                            )
                            # exponential backoff as recommended by AWS
                            # minimum wait is 10 minutes
                            retries += 1
                            self.timeout_with_printer(10 * 60 + 10 ** retries)
                        else:
                            print(
                                f"\n\nUnknown error occurred it was: {error}"
                            )
                            # we do not know what error it is
                            exit(1)  # TODO proper error handling

            if jobs_to_run:
                timeout = 60
                message = f"\r{jobs_done}/{all_jobs} jobs submitted. Instance limit reached, pausing for {timeout} seconds"
                self.timeout_with_printer(timeout, message)
        print(f"\r{all_jobs}/{all_jobs} jobs submitted successfully")
        return responses
