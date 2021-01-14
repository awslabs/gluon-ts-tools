import hashlib
import json
import yaml

from datetime import datetime
from functools import partial, singledispatch
from itertools import chain

from runtool import config_converter, config_parser, paths
from runtool.datatypes import *
from runtool.dispatcher import JobsDispatcher
from runtool.dryrun import generate_dry_run_table
from runtool.local_runner import run_training_on_local_machine
from runtool.utils import update_nested_dict


def hash(data):
    """
    Reproducible hash
    """
    return str(hashlib.sha1(str(data).encode("UTF-8")).hexdigest()[:8])


def set_dict_from_path(dictionary, path, value):
    path = path.split(".")
    current = dictionary
    while len(path) > 0:
        key = path.pop(0)
        if len(path) == 0:
            current[key] = value
        elif key in current:
            current = current[key]
        else:
            current[key] = {}
            current = current[key]


class Config(DotDict):
    def __init__(self, versions):
        base = {}
        for ver in versions:
            for key, value in ver.items():
                value = config_converter.infer_type(value)
                if key not in base:
                    base[key] = value
                else:
                    if not type(base[key]) is Versions:
                        if base[key] != value:
                            base[key] = Versions([base[key], value])
                    elif not value in base[key].versions:
                        base[key].versions.append(value)
                    else:
                        pass  # the same value is already added to the versions

        self.update(DotDict(base))


class Client:
    role = None
    bucket = None
    session = None
    dispatcher = None

    def __init__(self, role_arn, bucket, session):
        self.role = role_arn
        self.bucket = bucket
        self.session = session
        self.creation_time = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        self.dispatcher = JobsDispatcher(session)

    def convert_to_sagemaker_json(
        self, trial, experiment_name, runs, job_name_expression, tags
    ):
        # the run configuration uniquely describes
        # the dataset and algorithm combination of the trial
        # Of some reason, doing hash(trial) is non deterministic
        # below is a temporary workaround which makes the run_configuration determenistic
        trial_id = "".join(
            (
                trial["algorithm"]["image"],
                trial["algorithm"]["instance"],
                json.dumps(
                    trial["algorithm"]["hyperparameters"], sort_keys=True
                )
                if "hyperparameters" in trial["algorithm"]
                else "",
                json.dumps(trial["dataset"], sort_keys=True),
            )
        )
        run_configuration = f"{experiment_name}_{hash(trial_id)}"

        if not tags:
            tags = {}
        if "tags" in trial["algorithm"]:
            tags.update(trial["algorithm"]["tags"])
        if "tags" in trial["dataset"]:
            tags.update(trial["dataset"]["tags"])
        tags.update(
            {
                "run_configuration_id": run_configuration,  # identifies dataset/algorithm used
                "started_with_runtool": True,  # identifies that runtool started this job
                "experiment_id": experiment_name,  # identifies the experiment the job belongs to
                "repeated_runs_group_id": hash(  # identifies groups of runs started together
                    run_configuration + str(datetime.now())
                ),
            }
        )
        tags = [
            {"Key": key, "Value": str(value)} for key, value in tags.items()
        ]

        metrics = []
        if "metrics" in trial["algorithm"]:
            metrics += [
                {"Name": key, "Regex": value}
                for key, value in trial["algorithm"]["metrics"].items()
            ]

        if "metrics" in trial["dataset"]:
            metrics += [
                {"Name": key, "Regex": value}
                for key, value in trial["dataset"]["metrics"].items()
            ]

        hyperparameters = (
            trial["algorithm"]["hyperparameters"]
            if "hyperparameters" in trial["algorithm"]
            else {}
        )

        # extract path and value to override
        override_paths = {}
        for item in ["dataset", "algorithm"]:
            override_paths.update(
                {
                    key.lstrip("$sagemaker."): value
                    for key, value in trial[item].items()
                    if key.startswith("$sagemaker.")
                }
            )
        overrides = {}
        for path, value in override_paths.items():
            set_dict_from_path(overrides, path, value)

        for run_count in range(runs):
            job_name = (
                # evaluate user provided job name if provided
                config_parser.do_eval(
                    {"$eval": job_name_expression},
                    DotDict({"__trial__": trial}),
                )
                if job_name_expression
                # otherwise check for $job_name in trial
                else trial["algorithm"]["$job_name"]
                if "$job_name" in trial["algorithm"]
                else trial["dataset"]["$job_name"]
                if "$job_name" in trial["dataset"]
                # fallback on default naming
                else f"config-{hash(trial)}-date-{self.creation_time}-runid-{hash(run_configuration)}-run-{run_count}"
            )

            json_ = {
                "AlgorithmSpecification": {
                    "TrainingImage": trial["algorithm"]["image"],
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
                    for name, uri in trial["dataset"]["path"].items()
                ],
                "OutputDataConfig": {
                    "S3OutputPath": f"s3://{self.bucket}/{experiment_name}/{run_configuration}"
                },
                "ResourceConfig": {
                    "InstanceCount": 1,
                    "InstanceType": trial["algorithm"]["instance"],
                    "VolumeSizeInGB": 32,
                },
                "StoppingCondition": {"MaxRuntimeInSeconds": 86400},
                "RoleArn": self.role,
                "TrainingJobName": f"{job_name}",
                "Tags": [
                    *tags,
                    {"Key": "run_number", "Value": str(run_count)},
                    {"Key": "number_of_runs", "Value": str(runs)},
                ],
            }

            # apply user overrides
            yield update_nested_dict(json_, overrides)

    def generate_sagemaker_jsons(
        self,
        experiments: Experiments,
        experiment_name: str = "default name",
        runs: int = 1,
        job_name_expression: str = None,
        tags: dict = None,
    ):
        assert isinstance(
            experiments,
            (
                Experiment,
                Experiments,
            ),
        )
        experiments = expand(experiments)

        # generate sagemaker compliant jsons
        generators = (
            self.convert_to_sagemaker_json(
                exp, experiment_name, runs, job_name_expression, tags
            )
            for exp in experiments
        )

        return (sm_json for generator in generators for sm_json in generator)

    def run(
        self,
        combination: Experiments,
        experiment_name: str = "default_name",
        runs: int = 1,
        job_name_expression: str = None,
        tags: dict = None,
    ):
        sm_jsons = self.generate_sagemaker_jsons(
            combination, experiment_name, runs, job_name_expression, tags
        )

        responses = self.dispatcher.dispatch(sm_jsons)

        return list(responses.keys())

    def dry_run(
        self,
        combination: Experiments,
        experiment_name: str = "default_name",
        runs: int = 1,
        job_name_expression: str = None,
        tags: dict = None,
        print_table=True,
    ):
        sm_jsons = self.generate_sagemaker_jsons(
            combination, experiment_name, runs, job_name_expression, tags
        )
        return generate_dry_run_table(sm_jsons, print_table)

    def local_run(
        self,
        combination: Experiments,
        output_dir: str,
        experiment_name: str = "default_name",
        runs: int = 1,
        job_name_expression: str = None,
        tags: dict = None,
    ):
        sm_jsons = self.generate_sagemaker_jsons(
            combination, experiment_name, runs, job_name_expression, tags
        )
        return run_training_on_local_machine(
            sm_jsons,
            output_dir,
        )

    def as_yaml(
        self,
        combination: Experiments,
        experiment_name: str = "default_name",
        runs: int = 1,
        job_name_expression: str = None,
        tags: dict = None,
    ):
        return yaml.dump(
            list(
                self.generate_sagemaker_jsons(
                    combination,
                    experiment_name,
                    runs,
                    job_name_expression,
                    tags,
                )
            ),
            indent=3,
        )


@singledispatch
def load_config(data):
    if not isinstance(data, dict):
        raise TypeError("the root node of the config has to be a dict")

    data = config_parser.apply_transformations(data)
    data = [config_converter.convert_to_types(node) for node in data]

    return Config(data)


@load_config.register
def load_config_path(data: str):
    with open(data) as f:
        data = yaml.safe_load(f)
    return load_config(data)


@singledispatch
def expand(experiment: Experiment):
    return DotDict(
        config_parser.recursive_apply(
            experiment,
            partial(config_parser.do_trial, locals={"__trial__": experiment}),
        )
    )


@expand.register
def expand_experiments(data: Experiments):
    return (expand(exp) for exp in data)
