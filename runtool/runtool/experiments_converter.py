import json
from datetime import datetime
from functools import partial, singledispatch
from hashlib import sha1
from itertools import chain
from typing import DefaultDict, Iterable, Optional

from pydantic import BaseModel

from runtool.datatypes import DotDict, Experiment, Experiments
from runtool.recurse_config import recursive_apply
from runtool.transformations import apply_trial
from runtool.utils import update_nested_dict
from toolz.dicttoolz import valmap


def hash(data):
    """
    Reproducible hash
    """
    return str(sha1(str(data).encode("UTF-8")).hexdigest()[:8])


class ExperimentConverter(BaseModel):
    experiment: dict
    tags: dict
    runs: int
    experiment_name: str
    tags: dict
    creation_time: str
    bucket: str
    role: str
    job_name_expression: Optional[str]

    def generate_tags(self, run_configuration: str) -> list:
        tags = self.experiment["algorithm"].get("tags", {})
        tags.update(self.experiment["dataset"].get("tags", {}))
        tags.update(
            {
                "run_configuration_id": run_configuration,  # identifies dataset/algorithm used
                "started_with_runtool": True,  # identifies that runtool started this job
                "experiment_name": self.experiment_name,  # identifies the experiment the job belongs to
                "repeated_runs_group_id": hash(  # identifies groups of runs started together
                    run_configuration + str(datetime.now())
                ),
                "number_of_runs": str(self.runs),
            }
        )
        tags.update(self.tags)

        return [
            {"Key": key, "Value": str(value)} for key, value in tags.items()
        ]

    def calculate_run_configuration(self) -> str:
        # the run configuration uniquely describes
        # the dataset and algorithm combination of the trial
        # Of some reason, doing hash(trial) is non deterministic
        # below is a temporary workaround which makes the run_configuration determenistic
        trial_id = "".join(
            (
                self.experiment["algorithm"]["image"],
                self.experiment["algorithm"]["instance"],
                json.dumps(
                    self.experiment["algorithm"]["hyperparameters"],
                    sort_keys=True,
                )
                if "hyperparameters" in self.experiment["algorithm"]
                else "",
                json.dumps(self.experiment["dataset"], sort_keys=True),
            )
        )
        return f"{self.experiment_name}_{hash(trial_id)}"

    def generate_metrics(self) -> list:
        return [
            {"Name": key, "Regex": value}
            for key, value in chain(
                self.experiment["algorithm"].get("metrics", {}).items(),
                self.experiment["dataset"].get("metrics", {}).items(),
            )
        ]

    def generate_sagemaker_overrides(self) -> dict:
        """
        if a key looks like $sagemaker.<some path> within the
        algorithm or dataset, the final sagemaker json should
        have the value of <some path> set to the value of the
        dictionary item with key $sagemaker.<some path>.

        i.e.

        {$sagmaker.hello.world: 10}

        will result in that in the JSON sent to SageMaker will
        be updated with the following item:

        {"hello" {"world": 10}}

        """
        # generate tuple of format: Tuple[List, Any]
        # this tuple will only contain items having
        # a key which starts with "$sagemaker."
        # i.e.
        # {"$sagemaker.hello.world": 10, "smth": 2}
        # generates:
        # (["hello", "world"], 10)

        sagemaker_overrides = (
            (key.lstrip("$sagemaker.").split("."), value)
            for key, value in chain(
                self.experiment["algorithm"].items(),
                self.experiment["dataset"].items(),
            )
            if key.startswith("$sagemaker.")
        )

        # generate a dictionary from the tuple
        # (["hello", "world"], 10)
        # ->
        # {"hello" {"world": 10}}
        overrides = DefaultDict(dict)
        for path, value in sagemaker_overrides:
            current = overrides
            while path:
                key = path.pop(0)
                if not path:
                    current[key] = value
                else:
                    current = current[key]
        return dict(overrides)

    def generate_job_name(self, run: int, run_configuration: str) -> str:
        """
        Generates a training job name for a sagemaker job.
        User provided jobnames passed to the ExperimentConverter has priority
        thereafter any $job_name keys in the algorithm or dataset will be
        used. If none exists, a default training job name will be generated.
        """
        # user naming convention has highest priority
        if self.job_name_expression:
            return apply_trial(
                node={"$eval": self.job_name_expression},
                locals=DotDict(
                    dict(
                        __trial__=self.experiment,
                        run=run,
                        run_configuration=run_configuration,
                    )
                ),
            )

        # thereafter any jobnames added within the config has prio
        elif "$job_name" in self.experiment["algorithm"]:
            return self.experiment["algorithm"]["$job_name"]
        elif "$job_name" in self.experiment["dataset"]:
            return self.experiment["dataset"]["$job_name"]

        # fallback on default naming
        return (
            f"config-{hash(self.experiment)}"
            f"-date-{self.creation_time}"
            f"-runid-{hash(run_configuration)}"
            f"-run-{run}"
        )

    def generate_hyperparameters(self) -> dict:
        return {
            key: str(
                value
            )  # important to cast to string sagemaker to avoid sagemaker crash
            for key, value in self.experiment["algorithm"]
            .get("hyperparameters", {})
            .items()
        }

    def run(self) -> Iterable[dict]:
        run_configuration = self.calculate_run_configuration()
        tags = self.generate_tags(run_configuration)
        metrics = self.generate_metrics()
        hyperparameters = self.generate_hyperparameters()
        overrides = self.generate_sagemaker_overrides()

        for run in range(self.runs):
            job_name = self.generate_job_name(run, run_configuration)
            json_ = {
                "AlgorithmSpecification": {
                    "TrainingImage": self.experiment["algorithm"]["image"],
                    "TrainingInputMode": "File",
                    "MetricDefinitions": metrics,
                },
                "HyperParameters": {
                    key: str(value) for key, value in hyperparameters.items()
                },
                "InputDataConfig": [
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
                ],
                "OutputDataConfig": {
                    "S3OutputPath": f"s3://{self.bucket}/{self.experiment_name}/{run_configuration}"
                },
                "ResourceConfig": {
                    "InstanceCount": 1,
                    "InstanceType": self.experiment["algorithm"]["instance"],
                    "VolumeSizeInGB": 32,
                },
                "StoppingCondition": {"MaxRuntimeInSeconds": 86400},
                "RoleArn": self.role,
                "TrainingJobName": f"{job_name}",
                "Tags": [
                    *tags,
                    {"Key": "run_number", "Value": str(run)},
                ],
            }

            # apply any custom sagemaker json
            yield update_nested_dict(json_, overrides)


@singledispatch
def generate_sagemaker_json(
    experiment: Experiment,
    runs: int,
    experiment_name: str,
    job_name_expression: str,
    tags: dict,
    creation_time: str,
    bucket: str,
    role: str,
) -> Iterable[dict]:
    # recurse_config cannot handle UserDict and UserList
    # Thus convert experiment to a normal dict
    experiment = experiment.to_dict()

    # resolve $trial in experiments
    experiment = DotDict(
        recursive_apply(
            experiment, partial(apply_trial, locals={"__trial__": experiment})
        )
    )

    # generate jsons for calling the sagemaker api
    converter = ExperimentConverter(
        experiment=experiment,
        runs=runs,
        experiment_name=experiment_name,
        job_name_expression=job_name_expression,
        tags=tags,
        creation_time=creation_time,
        bucket=bucket,
        role=role,
    )
    return converter.run()


@generate_sagemaker_json.register
def generate_sagemaker_json_multiple(
    experiments: Experiments, **kwargs
) -> Iterable[dict]:
    return chain.from_iterable(
        generate_sagemaker_json(experiment, **kwargs)
        for experiment in experiments
    )
