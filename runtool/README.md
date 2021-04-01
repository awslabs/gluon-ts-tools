# Runtool
The Runtool is a tool for running large scale experiments on AWS SageMaker. 

## Installation
```bash
pip install -e .
```

## QuickStart

These two steps are required to use the runtool.

2. Create a `config.yml` file which describes your algorithms and datasets
3. Create a python script using the runtool

Below is an example `config.yml`

```yaml
my_ds:
    path:
        train: s3://my_bucket/my_data.json
        test: s3://my_bucket/my_test_data.json

my_algo:
    image: my_ecr_docker_image
    instance: ml.m5.xlarge
    hyperparameters:
        ...
```

Example of a python script for defining and executing jobs in SageMaker via the runtool.

```python
import boto3
from runtool import load_config, Client

# load config file
config = runtool.load_config("config.yml")

# create an experiment
my_experiment = config.my_ds * config.my_algo

# initialize runtool
tool = runtool.Client(
    role="arn:aws:iam::012345678901:role/service-role/my_role",
    bucket="my_bucket",
    session=boto3.Session(),
)

# dispatch the jobs
jobs = tool.run(my_experiment)
```

## Additional materials

* Step by step tutorials are available in [examples/tutorials](examples/tutorials). 
* For a walkthrough of writing `config.yml` files see [examples/writing_configs.md](examples/writing_configs.md)
* For runnable examples see [examples/runnable_examples](examples/runnable_examples)
