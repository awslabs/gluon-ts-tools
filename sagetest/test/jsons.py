import datetime
from dateutil.tz import tzlocal


JOB_JSON_1 = {
    "TrainingJobName": "dummy-job-1",
    "TrainingJobArn": "arn:aws:sagemaker:eu-west-1:1234",
    "ModelArtifacts": {"S3ModelArtifacts": "s3://bucket/path/model.tar.gz"},
    "TrainingJobStatus": "Completed",
    "SecondaryStatus": "Completed",
    "HyperParameters": {
        "distr_output": '{"__kind__": "instance","class": "gluonts.mx.distribution.NegativeBinomialOutput","args": [],"kwargs": {}}',
        "forecaster_name": "gluonts.model.deepar.DeepAREstimator",
        "freq": "1H",
        "prediction_length": "24",
    },
    "AlgorithmSpecification": {
        "TrainingImage": "12345678901.dkr.ecr.eu-west-1.amazonaws.com/gluonts:latest",
        "TrainingInputMode": "File",
        "MetricDefinitions": [
            {"Name": "abs_error", "Regex": " abs_error\\): (\\d+\\.\\d+)"},
            {"Name": "MASE", "Regex": " MASE\\): (\\d+\\.\\d+)"},
        ],
        "EnableSageMakerMetricsTimeSeries": False,
    },
    "RoleArn": "arn:aws:iam::12345678901:role/service-role/some-role",
    "InputDataConfig": [
        {
            "ChannelName": "train",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": "s3://bucket/dataset_path/train.json",
                    "S3DataDistributionType": "ShardedByS3Key",
                }
            },
            "CompressionType": "None",
            "RecordWrapperType": "None",
            "InputMode": "File",
        },
        {
            "ChannelName": "test",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": "s3://bucket/dataset_path/test.json",
                    "S3DataDistributionType": "ShardedByS3Key",
                }
            },
            "CompressionType": "None",
            "RecordWrapperType": "None",
            "InputMode": "File",
        },
    ],
    "OutputDataConfig": {
        "KmsKeyId": "",
        "S3OutputPath": "s3://bucket/output_path",
    },
    "ResourceConfig": {
        "InstanceType": "ml.c5.2xlarge",
        "InstanceCount": 1,
        "VolumeSizeInGB": 32,
    },
    "StoppingCondition": {"MaxRuntimeInSeconds": 86400},
    "CreationTime": datetime.datetime(
        2021, 5, 21, 7, 19, 25, tzinfo=tzlocal()
    ),
    "TrainingStartTime": datetime.datetime(
        2021, 5, 21, 7, 21, 11, tzinfo=tzlocal()
    ),
    "TrainingEndTime": datetime.datetime(
        2021, 5, 21, 7, 34, 32, tzinfo=tzlocal()
    ),
    "LastModifiedTime": datetime.datetime(
        2021, 5, 21, 7, 34, 32, tzinfo=tzlocal()
    ),
    "FinalMetricDataList": [
        {
            "MetricName": "abs_error",
            "Value": 12105318.0,
            "Timestamp": datetime.datetime(
                2021, 5, 21, 7, 34, 22, tzinfo=tzlocal()
            ),
        },
        {
            "MetricName": "MASE",
            "Value": 0.9552038311958313,
            "Timestamp": datetime.datetime(
                2021, 5, 21, 7, 34, 22, tzinfo=tzlocal()
            ),
        },
    ],
    "EnableNetworkIsolation": False,
    "EnableInterContainerTrafficEncryption": False,
    "EnableManagedSpotTraining": False,
    "TrainingTimeInSeconds": 801,
    "BillableTimeInSeconds": 801,
    "Tags": [
        {"Key": "config_id", "Value": "default_benchmark_name/1234"},
        {"Key": "dataset_id", "Value": "electricity"},
    ],
}

JOB_JSON_2 = {
    "TrainingJobName": "dummy-job-2",
    "TrainingJobArn": "arn:aws:sagemaker:eu-west-1:1234",
    "ModelArtifacts": {"S3ModelArtifacts": "s3://bucket/path/model.tar.gz"},
    "TrainingJobStatus": "Completed",
    "SecondaryStatus": "Completed",
    "HyperParameters": {
        "prediction_length": "24",
    },
    "AlgorithmSpecification": {
        "TrainingImage": "12345678901.dkr.ecr.eu-west-1.amazonaws.com/gluonts:latest",
        "TrainingInputMode": "File",
        "MetricDefinitions": [
            {"Name": "abs_error", "Regex": " abs_error\\): (\\d+\\.\\d+)"},
            {"Name": "MASE", "Regex": " MASE\\): (\\d+\\.\\d+)"},
        ],
        "EnableSageMakerMetricsTimeSeries": False,
    },
    "RoleArn": "arn:aws:iam::12345678901:role/service-role/some-role",
    "InputDataConfig": [
        {
            "ChannelName": "train",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": "s3://bucket/dataset_path/train.json",
                    "S3DataDistributionType": "ShardedByS3Key",
                }
            },
            "CompressionType": "None",
            "RecordWrapperType": "None",
            "InputMode": "File",
        },
        {
            "ChannelName": "test",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": "s3://bucket/dataset_path/test.json",
                    "S3DataDistributionType": "ShardedByS3Key",
                }
            },
            "CompressionType": "None",
            "RecordWrapperType": "None",
            "InputMode": "File",
        },
    ],
    "OutputDataConfig": {
        "KmsKeyId": "",
        "S3OutputPath": "s3://bucket/output_path",
    },
    "ResourceConfig": {
        "InstanceType": "ml.c5.2xlarge",
        "InstanceCount": 1,
        "VolumeSizeInGB": 32,
    },
    "StoppingCondition": {"MaxRuntimeInSeconds": 86400},
    "CreationTime": datetime.datetime(
        2021, 5, 21, 7, 19, 25, tzinfo=tzlocal()
    ),
    "TrainingStartTime": datetime.datetime(
        2021, 5, 21, 7, 21, 11, tzinfo=tzlocal()
    ),
    "TrainingEndTime": datetime.datetime(
        2021, 5, 21, 7, 34, 32, tzinfo=tzlocal()
    ),
    "LastModifiedTime": datetime.datetime(
        2021, 5, 21, 7, 34, 32, tzinfo=tzlocal()
    ),
    "FinalMetricDataList": [
        {
            "MetricName": "abs_error",
            "Value": 100,
            "Timestamp": datetime.datetime(
                2021, 5, 21, 7, 34, 22, tzinfo=tzlocal()
            ),
        },
        {
            "MetricName": "MASE",
            "Value": 1,
            "Timestamp": datetime.datetime(
                2021, 5, 21, 7, 34, 22, tzinfo=tzlocal()
            ),
        },
    ],
    "EnableNetworkIsolation": False,
    "EnableInterContainerTrafficEncryption": False,
    "EnableManagedSpotTraining": False,
    "TrainingTimeInSeconds": 10,
    "BillableTimeInSeconds": 10,
    "Tags": [
        {"Key": "config_id", "Value": "dummy"},
        {"Key": "dataset_id", "Value": "dummy2"},
    ],
}
