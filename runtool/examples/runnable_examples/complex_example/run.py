import boto3
import runtool

config = runtool.load_config("complex.yml")

experiment = config.algorithms * config.datasets

tool = runtool.Client(
    role_arn="arn:aws:iam::012345678901:role/service-role/AmazonSageMaker-ExecutionRole",
    bucket="my_bucket",
    session=boto3.Session(),
)

tool.dry_run(experiment)
# jobs = tool.run(experiment)
