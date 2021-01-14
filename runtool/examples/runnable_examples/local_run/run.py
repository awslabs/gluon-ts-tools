import boto3
import runtool

config = runtool.load_config("local.yml")

experiment = config.algorithms * config.datasets

# this should be removed for the local mode
tool = runtool.Client(
    role_arn="",
    bucket="",
    session=boto3.Session(),
)

tool.dry_run(experiment)
runs = tool.local_run(
    experiment, output_dir="/Users/freccero/local_sagemaker_output"
)

# contains the paths to the outputs
print(runs)
