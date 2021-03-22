# Writing configuration files
Here we describe what constitutes a config file and how these can be used to generate experiments using the runtool. 

A config file has 6 components, each of which are optional. 

* `Algorithm`
* `Dataset`
* `Experiment`
* `Algorithms` (a list of `Algorithm` objects)
* `Datasets` (list of `Dataset` objects)
* `Experiments` (list of `Experiment`)

When the runtool loads the config file, it finds these components in the config and uses them 
to generate `Experiments` which can be used to start training jobs on SageMaker.

## General structure

An `Algorithm` has the following structure:

```yaml
my_algorithm: 
    # obligatory
    image: str, the docker image to use
    instance: str, the SageMaker instance to execute the algorithm on

    # optional
    hyperparameters: dict, the hyperparameters to use, i.e.
        # example
        epochs: 10 
    tags: dict, the tags to apply to the job in SageMaker
        #example
        my_tag: my_value!
    metrics: dict, regexes and names of metrics that SageMaker should track
        #example
        abs_error: 'abs_error\): (\d+\.\d+)'
```

A `Dataset` has the following structure:

```yaml
my_dataset:
    #obligatory
    path: dict, channels for different phases of training, i.e.
        # example
        my_channel: s3://my_bucket/train.json

    #optional
    meta: dict, contains meta information about your dataset, i.e. 
        # example
        freq: H 
    tags: dict, the tags to apply to the job in SageMaker
        #example
        my_tag: my_value!
```

An `Experiment` is a container for one Algorithm and one Dataset

```yaml
my_experiment:
    #obligatory
    algorithm:
        ... # an Algorithm
    dataset:
        ... # a Dataset
```

## Operators
Configuration files can make use of certain operators to calculate values when defining experiments. In this section these operators will be presented. 

The operators are:

* [$from](#from)
* [$eval](#eval)
* [$trial](#trial)
* [$each](#each)
* [$ref](#ref)
* [$job_name](#job_name)

### $from
The `$from` operator enable inheritance of values from other nodes in the configuration file. 

In the example config below, three hyperparameter configurations of an algorithm is shown. The difference between the three algorithm configurations are some changes in their hyperparameters. 

```yaml
algo_1:
    image: my_image:latest
    instance: ml.m5.xlarge
    hyperparameters:
        epochs: 10
        freq: H
        layers: 5
        prediction_length: 7
algo_2:
    image: my_image:latest
    instance: ml.m5.xlarge
    hyperparameters:
        epochs: 10
        freq: H
        layers: 5
        prediction_length: 14
algo_3:
    image: my_image:latest
    instance: ml.m5.xlarge
    hyperparameters:
        epochs: 10
        freq: H
        layers: 10
        prediction_length: 14
```

By using the `$from` operator, the above example can be simplified to:

```yaml
algo_1:
    image: my_image:latest
    instance: ml.m5.xlarge
    hyperparameters:
        epochs: 10
        freq: H
        layers: 5
        prediction_length: 7
algo_2:
    $from: algo_1
    hyperparameters:
        prediction_length: 14
algo_3: 
    $from: algo_2
    hyperparameters:
        layers: 10
```

### $eval
`$eval` allows setting values in the config dynamically during runtime using python code.

example:
```yaml
my_algo:
    ...
    hyperparameters:
        prediction_length: 1
        context_length: 
            $eval: sum([1,2,3,4])
```

The `$trial` tag can be inserted into a `$eval` statement to refer to the current `Experiment`.  

An example may help.
Assume you are running an algorithm on `N` datasets. You want to set a hyperparameter of the algorithm to some value depending on the dataset used. 
Below we set the `freq` parameter to the value of `meta.freq` of whichever dataset `algo` is combined with.

```yaml
algo:
    ... 
    hyperparameters:
        freq: 
            $eval: $trial.dataset.meta.freq

dataset_1:
    ...
    meta: 
        freq: D

dataset_2:
    ...
    meta: 
        freq: H
```

For the experiment where `algo` is run on the dataset `dataset_1`, `algo` will have the `freq` hyperparameter set to `D`. When `algo` instead is run on `dataset_2`, `algo` will have the hyperparameter `freq` set to `H`. 

### $each
`$each` generates multiple versions of a node, in the example below, `$each` is used to run an algorithm with three different images. 

```yaml
algo:
    ...
    image: 
        $each:
            - my_image:latest
            - my_image:1.0
            - my_image:0.1

my_ds:
    ...
```

When an experiment is generated using `algo` the `$each` will be calculated and the experiment will contain the corresponding amount of jobs. 
i.e. when running `config.algo * config.my_ds` the resulting experiment will contain the three versions of `algo` each running on `my_ds` but with different images.

1. `image: my_image:latest` 
2. `image: my_image:1.0` 
3. `image: my_image:0.1` 

### $ref
`$ref` is used to reference different parts of the config file. 

```yaml
my_value: 10
copy: 
    $ref: my_value # evaluates to 10
```

### $job_name
The `$job_name` tag is used to generate a custom name to the training jobs being created. 
This tag is only taken into account when placed inside of either an algorithm or a dataset. 

### $sagemaker
For customizing the json which is used to create sagemaker training jobs over the API one can use the `$sagemaker` tag. 
Please see the [documentation](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateTrainingJob.html) of the SageMaker CreateTrainingJob API for further information. 

```yaml
algo:
    $sagemaker.TrainingJobName: my-training-job-name
    $sagemaker.StoppingCondition.MaxRuntimeInSeconds: 100
```

### Multiple files
For organizing your project, you can load several different config files. For example it may be convenient to seperate your algorithms and your datasets into individual files. The runtool can then load these files as seperate configs as in the example below.

```yaml
#algorithms.yml
my_algo:
    ...
    tags:
        my_tag:
            $eval: my_algo running on the dataset $trial.dataset
```

```yaml
#datasets.yml
my_dataset:
    ...
```

```python
# run.py
import runtool

algorithms = runtool.load_config("algorithms.yml")
datasets = runtool.load_config("datasets.yml")

experiment = algorithms.my_algo * datasets.my_dataset

...

```
