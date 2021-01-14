# Writing configuration files
In this file we describe what constitutes a config file and the functionality which runtools offers when parsing them. 

## General structure
A config file can at the minimum contain information about an algorithm or a dataset. There is no upper limit on how many Algorithms and datasets it can contain. 

An algorithm has the following structure:

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

A dataset has the following structure:

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

## Operators
Configuration files can make use of certain operators to allow for dynamic calculation of values upon defining experiments. In this section these will be presented. 

The operators are:

* [$from](#from)
* [$eval](#eval)
* [$trial](#trial)
* [$each](#each)
* [$ref](#ref)
* [$job_name](#job_name)

### $from
The `$from` operator enable inheritance of values from other nodes in the configuration file. 

In the example confg below, three different hyperparameter configurations of an algorithm is shown. As you see the only change between the three algorithm configurations are slight changes in the hyperaparameters they take. 

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
`$eval` allows setting values in the config dynamically during runtime using python code. The functions in the math package can be used as in the example below. 

example:
```yaml
my_algo:
    ...
    hyperparameters:
        prediction_length: 1
        context_length: 
            $eval: ceil(5 * SimpleFeedForward.hyperparameters.epochs / 3)  # results in the value 2

```

The `$trial` tag can be inserted into a `$eval` statement in order to refer to the specific combination of algorithm and dataset which will be used. 
By using `$trial` you can access the dataset and the algortihm used in an exeperiment by writing `$trial.dataset` and `$trial.algorithm`.

An example may help.
Assume you are running an algorithm on N different datasets. You want to set a hyperparameter of the algorithm to some value depending on the datasett used. 
In the example below we set the `freq` parameter to what `freq` is set to inside of the `dataset.meta` 

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
If you want to try several different values of something in the yaml file, you may want to use `$each`. `$each` takes a list of values which it should resolve to. 
In the example below, we want an algorithm to be using three different images when run. I.e. it should run three times.

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

`$each` can also be nested and used multiple times for more advanced yaml generation.

```yaml
algo:
    ...
    image: 
        $each:
            - my_image:latest
            - my_image:1.0
            - my_image:0.1
    tags:
        my_tag:
            $each:
                - hello
                - good morning


my_ds:
    ...
```

This will result in 6 versions of `algo` 

1. `image: my_image:latest` & `hello`
2. `image: my_image:latest` & `good morning`
3. `image: my_image:1.0` & `hello`
4. `image: my_image:1.0` & `good morning`
5. `image: my_image:0.1` & `hello`
6. `image: my_image:0.1` & `good morning`


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
If `$job_name` is defined in both, then the name of the algorithm takes precedence.

### $sagemaker
For customizing the json which is used to create sagemaker training jobs over the API one can use the `$sagemaker` tag. 
Please see the [documentation](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateTrainingJob.html) of the SageMaker CreateTrainingJob API for further information. 

```yaml
algo:
    $sagemaker.TrainingJobName: my-training-job-name
    $sagemaker.StoppingCondition.MaxRuntimeInSeconds: 100
```

### Local mode
In order to run the training locally on your computer you need to provide a local dataset with the following syntax `file://path/to/my/dataset`. Furthermore, you also need to ensure that the docker image you want to use is available on your local machine. In order to run the system locally you should then use the `local_run` method of the `runtool.Client`. 
Further, the `role` and the `bucket` passed to the `runtool` during initalization can be left as empty strings. Any instance defined in the `Algorithms` used will be ignored when run locally. 

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
