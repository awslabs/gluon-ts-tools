import boto3
import runtool

# load config file
config = runtool.load_config("large.yml")

# create an experiment
experiment = config.algorithms * config.datasets

# dispatch jobs
tool = runtool.Client(
    role_arn="arn:aws:iam::012345678901:role/service-role/AmazonSageMaker-ExecutionRole",
    bucket="my_bucket",
    session=boto3.Session(),
)

tool.dry_run(experiment)
# jobs = tool.run(experiment)  # blocking call
