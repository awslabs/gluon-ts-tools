# The Runtool 

The runtool is a python package which makes it easy to define and execute SageMaker Training jobs in a reproducible way. 

Algorithms and datasets which are to be executed on SageMaker are described using YAML in reusable configuration files. By loading these files using the runtool it is possible to map algorithms to be trained onto datasets to train on using simple operators such as `+` and `*`.  


## Installation
The runtool 

```bash
pip install -e .
```
Thereafter you should be able to import the runtool into your python project 

```python
import runtool
```

For examples of how to use the runtool please see the [examples](./examples) and the [Quickstart](#quickstart) section below.

## Requirements 
### For running on SageMaker
* A [SageMaker compatible](https://docs.aws.amazon.com/sagemaker/latest/dg/docker-containers.html) docker image on AWS ECR containing the algorithm which should be trained. 
  * Gluon-TS has compatible dockerfiles available in the Gluon-TS repository.
* A dataset to train the image on in an S3 bucket
* An AWS IAM Role with the following permissions
  * Starting training jobs
  * Read and write access to S3 buckets
  * Read access to the EC2 container registry

### For running locally
* A [SageMaker compatible](https://docs.aws.amazon.com/sagemaker/latest/dg/docker-containers.html) docker image containing the algorithm to be trained.
* A dataset to train the image on


## Quickstart
This simple example shows how one can write a configuration file and how to use the runtool to dispatch training jobs using it. For more complex examples, please take a look at the instructions and examples in [/examples/writing_configs.md](./examples/writing_configs.md).

The first step is to define a config file (`config.yml`) containing the algorithms and datasets which we want to run. In this example we define one dataset and one algorithm. An algorithm needs to contain atleast an image containing the algorithm to run and an instance while a dataset has to contain atleast the paths to the dataset.

```YAML
my_dataset:
    meta: # Meta information describing the dataset
        freq: D
        prediction_length: 7
    path: # Paths to the dataset
        train: s3://my_bucket/datasets/my_dataset/train/data.json
        test: s3://my_bucket/datasets/my_dataset/test/data.json

my_algorithm:
    image: 0123456789012.dkr.ecr.eu-west-1.amazonaws.com/my_repo:my_tag
    instance: ml.m5.xlarge
    hyperparameters:
        # we set the "prediction_length" and "freq" based on dataset meta information
        prediction_length: 
            $eval: $trial.dataset.meta.prediction_length # becomes 7 
        freq:
            $eval: $trial.dataset.meta.freq # becomes "D"
```

When the configuration file (`config.yml`) has been created, it is time to implement a python script which allows us to use this configuration file. 
We start by importing the runtool and loading the created config file into o2
We then use this loaded config to define an experiment we wish to run. This is done using the `*` operator. The runtool automatically detects that `my_algorithm` is an algorithm and that `my_dataset` is a dataset. Thus it infers when using the `*` that an experiment should be generated.

```python
my_experiment = config.my_algorithm * config.my_dataset
```

Now that we have an experiment we can then create a `runtool.Client` instance. The `runtool.Client` is used to dispatch jobs to SageMaker. The client requires a AWS Role with permission to start SageMaker training jobs and S3 access. 

```python
tool = runtool.Client(
    role_arn="arn:aws:iam::0123456789:role/service-role/my-sagemaker-execution-role",
    bucket="my_output_bucket",
    session=boto3.Session(),
)
```
We can then use this Client to investigate which jobs will be started through the `dry-run` functionality. By performing a `dry-run` we run the system without actually starting any jobs on SageMaker. This is useful to see that your experiment is as you expect. 

```python
tool.dry_run(my_experiment)
```

This results in a summary being printed out in the terminal. It should look similar to this.

```shell
+-------+-----------------+-------------+----------+----------+------+-----+----------+
| image | hyperparameters | output_path | instance | job_name | tags | run | datasets |
+-------+-----------------+-------------+----------+----------+------+-----+----------+
| ...   | ...             | ...         | ...      | ...      | ...  | ... | ...      |
+-------+-----------------+-------------+----------+----------+------+-----+----------+
total number of jobs: 1
```

If you are want to start the training jobs on SageMaker all we need to do is to call `tool.run()`. The dispatching of jobs is currently done sequentially so for large workloads this call may take some time. `tool.run` also takes additional parameters which allows you to set additional runtime information such as how many times each training job should be run. `tool.run(...)` returns the names of the started training jobs. 

```python
jobs = tool.run(my_experiment, runs=5) # run my experiment five times on sagemaker
print(jobs) # ["job_name_1",..., "job_name_5"]
```

If you are starting multiple jobs which should run in parallel you may wish to increase the amount of training jobs you can run in parallel. See the [AWS quotas documentation](https://docs.aws.amazon.com/general/latest/gr/sagemaker.html#limits_sagemaker) for more info. 

## Further examples

