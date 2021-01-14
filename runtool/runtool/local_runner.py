from sagemaker.estimator import Estimator
from sagemaker.local import LocalSession


def run_training_on_local_machine(
    sm_jsons,
    output_path,
):
    if not output_path.startswith("file://"):
        output_path = f"file://{output_path}"
    print("running training jobs in local mode")
    paths = {}
    for run in sm_jsons:
        print(f"Starting next training job ({run['TrainingJobName']})\n")
        path_output = f'{output_path}/{run["TrainingJobName"]}'
        paths[run["TrainingJobName"]] = path_output
        inputs = {
            channel["ChannelName"]: channel["DataSource"]["S3DataSource"][
                "S3Uri"
            ]
            for channel in run["InputDataConfig"]
        }

        estimator = Estimator(
            image_uri=run["AlgorithmSpecification"]["TrainingImage"],
            role="arn:aws:iam::012345678901:role/service-role/local",  # dummy role to make it work
            instance_count=1,
            instance_type="local",
            output_path=path_output,
            tags=run["Tags"],
            metric_definitions=run["AlgorithmSpecification"][
                "MetricDefinitions"
            ],
            hyperparameters=run["HyperParameters"],
        )

        estimator.fit(inputs=inputs, job_name=run["TrainingJobName"])
    return paths
