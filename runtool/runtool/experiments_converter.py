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

import json
from datetime import datetime
from functools import partial
from hashlib import sha1
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Union

from pydantic import BaseModel, validator
from toolz.dicttoolz import update_in, valmap

from runtool.datatypes import DotDict, Experiment, Experiments
from runtool.recurse_config import recursive_apply
from runtool.transformations import apply_trial
from runtool.utils import update_nested_dict


class Job(BaseModel):
    """
    Contains data and methods for creating JSONs used when starting training
    jobs in SageMaker.
    """

    experiment: dict
    creation_time: str
    bucket: str
    role: str
    tags: Optional[dict] = {}
    runs: Optional[int] = 1
    experiment_name: Optional[str] = None
    job_name_expression: Optional[str] = None
    run_configuration: str = None

    @validator("run_configuration", always=True)
    def set_run_configuration(cls: "Job", _: str, values: dict):
        return cls.generate_run_configuration(values)

    @classmethod
    def generate_run_configuration(cls: "Job", job: dict) -> str:
        """
        The run configuration describes the dataset and algorithm of the job.

        This is done by hashing the image, instance type, hyperparameters and
        dataset of the job. The string this function returns has this format:

        "<experiment_name>_<hash>"

        """
        hyperparameters = job["experiment"]["algorithm"].get(
            "hyperparameters", ""
        )
        if hyperparameters:
            hyperparameters = json.dumps(hyperparameters, sort_keys=True)

        trial_id = "".join(
            (
                job["experiment"]["algorithm"]["image"],
                job["experiment"]["algorithm"]["instance"],
                hyperparameters,
                json.dumps(job["experiment"]["dataset"], sort_keys=True),
            )
        )
        return f"{job['experiment_name']}_{reproducible_hash(trial_id)}"

    def generate_tags(self) -> List[Dict[str, str]]:
        """
        Generates a list of tags where each tag has the format:

            {"Key": ..., "Value": ...}

        This list will be populated with any tags in `job.experiment`.
        Further some default tags are added which aids in identifying and grouping
        the started jobs:

        `run_configuration_id`
        Unique tag which identifies the algorithm, hyperparameters & dataset
        used in the job.

        `started_with_runtool`
        identifies that the runtool was used to start this job

        `experiment_name`
        The name of the experiment which this jobs is a part of.

        `repeated_runs_group_id`
        If a job should be run several times in an experiment each of the repeated
        runs of it will have the same `repeated_runs_group_id`.

        `number_of_runs`
        The number of times the job should be run.
        """
        tags = {}
        tags.update(self.experiment["algorithm"].get("tags", {}))
        tags.update(self.experiment["dataset"].get("tags", {}))
        tags.update(
            {
                "run_configuration_id": self.run_configuration,
                "started_with_runtool": True,
                "experiment_name": self.experiment_name,
                "repeated_runs_group_id": reproducible_hash(
                    self.run_configuration + str(datetime.now())
                ),
                "number_of_runs": str(self.runs),
            }
        )
        tags.update(self.tags)

        return [
            {"Key": key, "Value": str(value)} for key, value in tags.items()
        ]

    def generate_job_name(self, run: int) -> str:
        """
        Generates a training job name for a sagemaker job.

        There is a hierarchy of how a job should be named where any expression
        provided within the `job.job_name_expression` has highest priority.
        Thereafter if a `$job_name` key exists in `job.experiment["algorithm"]`
        or in `job.experiment["dataset"]` its value will be used.
        If no custom name has been provided, a default training job name is
        generated.
        """
        # user naming convention has highest priority
        if self.job_name_expression:
            return apply_trial(
                node={"$eval": self.job_name_expression},
                locals=DotDict(
                    dict(
                        __trial__=self.experiment,
                        run=run,
                        run_configuration=self.run_configuration,
                    )
                ),
            )

        # thereafter any jobnames added within the config has prio
        if "$job_name" in self.experiment["algorithm"]:
            return self.experiment["algorithm"]["$job_name"]

        # job names in the dataset has lower priority
        if "$job_name" in self.experiment["dataset"]:
            return self.experiment["dataset"]["$job_name"]

        # fallback on default naming
        return (
            f"config-{reproducible_hash(self.experiment)}"
            f"-date-{self.creation_time}"
            f"-runid-{reproducible_hash(self.run_configuration)}"
            f"-run-{run}"
        )

    def generate_datasets(self):
        return [
            {
                "ChannelName": name,
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": uri,
                    }
                },
            }
            for name, uri in self.experiment["dataset"]["path"].items()
        ]

    def generate_metrics(self) -> List[Dict[str, str]]:
        """
        Extracts any metric definitions in the algorithm and dataset of the
        experiment in the job. These metric definitions are then compiled into a
        list with the format required by SageMaker API.
        """
        return [
            {"Name": key, "Regex": value}
            for key, value in chain(
                self.experiment["algorithm"].get("metrics", {}).items(),
                self.experiment["dataset"].get("metrics", {}).items(),
            )
        ]

    def generate_sagemaker_overrides(self) -> Dict[str, Any]:
        """
        This function extracts items from the algorithm and the dataset where the
        key has the structure:

        `$sagemaker.<path>`.

        The extracted `<path>` is then used to populate a new `dict` where the
        value at `<path>` is set to that of the `$sagemaker.<path>` in the source.

        i.e.

        >>> job = Job( # doctest: +SKIP
        ...     experiment=dict(
        ...         algorithm={"$sagemaker.hello.world": 10},
        ...         dataset={"smth": 1}
        ...     ),
        ...     ...
        ... )
        >>> job.generate_sagemaker_overrides() == { # doctest: +SKIP
        ...     "hello": {"world": 10},
        ... }
        True

        """
        # generate tuple of format: Tuple[List, Any]
        # this tuple will only contain items having
        # a key starting with "$sagemaker."
        # i.e.
        # {"$sagemaker.hello.world": 10, "smth": 2}
        # ->
        # (["hello", "world"], 10)

        sagemaker_overrides = (
            (key.split(".")[1:], value)
            for key, value in chain(
                self.experiment["algorithm"].items(),
                self.experiment["algorithm"].items(),
            )
            if key.startswith("$sagemaker.")
        )

        # generate a dictionary from the tuple
        # (["hello", "world"], 10)
        # ->
        # {"hello": {"world": 10}}
        overrides = {}
        for path, value in sagemaker_overrides:
            overrides = update_in(overrides, path, lambda _: value)

        return overrides

    def generate_hyperparameters(self):
        return valmap(
            str, self.experiment["algorithm"].get("hyperparameters", {})
        )


def reproducible_hash(data):
    """
    Generate a hash which is reproducible across several runs of Python.

    The builtin `hash` method of Python generates different hashes during
    different runs of Python while the `reproducible_hash`always generates
    the same value.

    >>> reproducible_hash("hello")
    'aaf4c61d'
    >>> reproducible_hash({"foo": 1})
    '0c90a67c'
    """
    return str(sha1(str(data).encode("UTF-8")).hexdigest()[:8])


def generate_job_json(job: Job) -> Iterable[dict]:
    """Creates JSONs for starting training jobs in SageMaker."""

    run_configuration = job.run_configuration
    tags = job.generate_tags()
    datasets = job.generate_datasets()
    metrics = job.generate_metrics()
    overrides = job.generate_sagemaker_overrides()
    hyperparameters = job.generate_hyperparameters()

    s3_path = f"s3://{job.bucket}/{job.experiment_name}/{run_configuration}"

    for run in range(job.runs):
        job_name = job.generate_job_name(run)
        json_ = {
            "AlgorithmSpecification": {
                "TrainingImage": job.experiment["algorithm"]["image"],
                "TrainingInputMode": "File",
                "MetricDefinitions": metrics,
            },
            "HyperParameters": hyperparameters,
            "InputDataConfig": datasets,
            "OutputDataConfig": {"S3OutputPath": s3_path},
            "ResourceConfig": {
                "InstanceCount": 1,
                "InstanceType": job.experiment["algorithm"]["instance"],
                "VolumeSizeInGB": 32,
            },
            "StoppingCondition": {"MaxRuntimeInSeconds": 86400},
            "RoleArn": job.role,
            "TrainingJobName": job_name,
            "Tags": [
                *tags,
                {"Key": "run_number", "Value": str(run)},  # add current run
            ],
        }

        # apply any custom sagemaker json
        yield update_nested_dict(json_, overrides)


def generate_sagemaker_json(
    experiment: Union[Experiment, Experiments],
    runs: int,
    experiment_name: str,
    job_name_expression: str,
    tags: dict,
    creation_time: str,
    bucket: str,
    role: str,
) -> Iterable[dict]:
    """
    Converts an `Experiment` object into one or more dicts
    which can be used to start training jobs on SageMaker.

    Parameters
    ----------
    experiment
        A `runtool.datatypes.Experiment` object
    runs
        Number of times each job should be repeated
    experiment_name
        The name of the experiment
    job_name_expression
        A python expression which will be used to set
        the `TrainingJobName` field in the generated JSON.
    tags
        Any tags that should be set in the training job JSON
    creation_time
        The time which the current experiment was created.
        This needs to be passed as a single experiment run may contain
        multiple Experiment objects.
    bucket
        The AWS S3 bucket AWS SageMaker should use as an outputdirectory
        for storing model data.
    role
        The AWS IAM Role to use when starting training jobs

    Returns
    -------
    Iterable
        Dict
            JSON that can be used to create training jobs.
    """
    if isinstance(experiment, Experiments):
        return chain.from_iterable(
            generate_sagemaker_json(
                trial,
                runs,
                experiment_name,
                job_name_expression,
                tags,
                creation_time,
                bucket,
                role,
            )
            for trial in experiment
        )

    # we know here which algorithm is used with which dataset
    # thus we can now resolve $eval in the experiment.
    experiment = DotDict(
        recursive_apply(
            experiment.as_dict(),
            partial(apply_trial, locals=dict(__trial__=experiment)),
        )
    )

    # generate jsons for calling the sagemaker api
    return generate_job_json(
        Job(
            experiment=experiment,
            runs=runs,
            experiment_name=experiment_name,
            job_name_expression=job_name_expression,
            tags=tags,
            creation_time=creation_time,
            bucket=bucket,
            role=role,
        )
    )
