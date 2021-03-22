import boto3
import runtool.runtool as runtool

# load config file
config = runtool.load_config("minimum.yml")
# config = runtool.load_config("large.yml")
# config = runtool.load_config("complex.yml")

# create an experiment
my_experiment = config.algorithms * config.datasets

# initialize runtool
tool = runtool.Client(
    role="arn:aws:iam::012345678901:role/service-role/AmazonSageMaker-ExecutionRole",
    bucket="my_bucket",
    session=boto3.Session(),
)

# check what jobs are to be created
tool.dry_run(my_experiment)

# dispatch the jobs
# jobs = tool.run(my_experiment)  # blocking call
