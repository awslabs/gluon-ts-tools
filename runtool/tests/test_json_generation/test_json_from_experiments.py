from runtool.datatypes import Algorithm, Experiment, Dataset
from runtool.experiments_converter import generate_sagemaker_json
from datetime import datetime
import yaml

ALGORITHM = Algorithm(
    {
        "image": "012345678901.dkr.ecr.eu-west-1.amazonaws.com/gluonts/cpu:latest",
        "instance": "ml.m5.xlarge",
        "hyperparameters": {
            "prediction_length": 7,
            "freq": "D",
        },
    }
)

DATASET = Dataset(
    {
        "path": {
            "train": "s3://gluonts-run-tool/gluon_ts_datasets/constant/train/data.json",
            "test": "s3://gluonts-run-tool/gluon_ts_datasets/constant/test/data.json",
        }
    }
)

EXPERIMENT = Experiment.from_nodes(ALGORITHM, DATASET)


def compare(
    experiment,
    expected,
    runs=1,
    exp_name="test name",
    job_name=None,
    tags={},
    bucket="test bucket",
    creation_time="2021-02-19-17-11-33",
    role="test role",
    print_result=False,  # useful for debugging
):
    result = list(
        generate_sagemaker_json(
            experiment,
            runs=runs,
            experiment_name=exp_name,
            job_name_expression=job_name,
            tags=tags,
            bucket=bucket,
            creation_time=creation_time,
            role=role,
        )
    )
    for item in result:
        for tag in item["Tags"]:
            if tag["Key"] == "repeated_runs_group_id":
                tag["Value"] = "Mocked value"

    if print_result:
        print(yaml.dump(result))

    expected = yaml.safe_load(expected)
    assert result == expected


def test_simple():
    compare(
        experiment=EXPERIMENT,
        expected="""
        - 
            AlgorithmSpecification:
                MetricDefinitions: []
                TrainingImage: 012345678901.dkr.ecr.eu-west-1.amazonaws.com/gluonts/cpu:latest
                TrainingInputMode: File
            HyperParameters:
                freq: D
                prediction_length: '7'
            InputDataConfig:
                - 
                    ChannelName: train
                    DataSource:
                        S3DataSource:
                            S3DataType: S3Prefix
                            S3Uri: s3://gluonts-run-tool/gluon_ts_datasets/constant/train/data.json
                - 
                    ChannelName: test
                    DataSource:
                        S3DataSource:
                            S3DataType: S3Prefix
                            S3Uri: s3://gluonts-run-tool/gluon_ts_datasets/constant/test/data.json
            OutputDataConfig:
                S3OutputPath: s3://test bucket/test name/test name_5faa5d5d
            ResourceConfig:
                InstanceCount: 1
                InstanceType: ml.m5.xlarge
                VolumeSizeInGB: 32
            RoleArn: test role
            StoppingCondition:
                MaxRuntimeInSeconds: 86400
            Tags:
                - 
                    Key: run_configuration_id
                    Value: test name_5faa5d5d
                - 
                    Key: started_with_runtool
                    Value: 'True'
                - 
                    Key: experiment_name
                    Value: test name
                - 
                    Key: repeated_runs_group_id
                    Value: Mocked value
                - 
                    Key: number_of_runs
                    Value: '1'
                - 
                    Key: run_number
                    Value: '0'
            TrainingJobName: config-66684a57-date-2021-02-19-17-11-33-runid-50086f67-run-0
        """,
        print_result=True,
    )
