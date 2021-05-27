# Overview
Sagetest extends pytest to test SageMaker Training jobs. 

Below is a small example of how one can test wether the mean error across all training jobs with the same tag was below 100.

```python
import boto3
from sagetest import Filter, SageTest
sagetest = SageTest(boto3.Session())

@sagetest.fixture()
def my_jobs():
    return Filter(tags={"my_tag":"my_value"})

def test_my_jobs(my_jobs):
    assert my_jobs.metrics["<some_error>"].mean() < 100
```

## Installation
This will install SageTest and add it as a plugin to pytest.

```
pip install -e .
```

## QuickStart
SageTest uses filters to query SageMaker for training jobs. The [Filter](sagetest/search.py) class allows the definition of common filters. For complicated searches if the `sagetest.Filter` class is insufficient, then [*SageMaker Search Filters*](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_Filter.html) can be passed as a list to the `search_filters` parameter when creating a `sagetest.Filter` object. 

```python 
from sagetest import Filter
my_filter = Filter(
    names=["<job 1>", "<job 2>"], 
    tags={"<my tag>": "<my tag value>"}, 
    image="<my training job image>", 
    search_filters=[] # list of SageMaker Search Filter objects 
)
```


There are four ways of using SageTest:

1. Fixtures
1. Parametrizing tests
1. Using the CLI
1. Direct query

In the below sections examples of these are presented.

### Creating fixtures of SageMaker Training jobs
A sagetest fixture is created by decorating a function which returns a [Filter](sagetest/search.py) with the `@sagetest.fixture()` decorator. Sagetest replaces the Filters returned by the decorated function with training jobs matching the filters.

```python
# contents of conftest.py or test_<smth>.py
import boto3
from sagetest import Filter, SageTest

sagetest = SageTest(boto3.Session())

@sagetest.fixture()
def reference_job():
    return Filter(names=["<a training job name>"])
```

The created fixture can then be accessed in a test file as a normal pytest fixture.

```python
# contents of test_<smth>.py
def test_reference_job(reference_job):
    assert reference_job.metrics["<metric>"] < 100
```

### Parametrizing tests 
The `@sagetest.parametrize` decorator works just as the `pytest.parametrize` with the exception that any `Filter` objects in the parameters are replaced with their corresponding SageMaker Training jobs.

```python
# contents of test_<smth>.py
import boto3
from sagetest import Filter, SageTest

sagetest = SageTest(boto3.Session())

@sagetest.parametrize("jobs", [Filter(...), Filter(...)])
def test_jobs(jobs):
    assert jobs.all(lambda job: job.training_time < 100)
```

Additional non-`Filter` parameters are left unaltered. 

```python
@sagetest.parametrize(
    "foo, jobs, bar", 
    [
        (1, Filter(...), 2), 
        (2, Filter(...), 3),
    ]
)
def test_jobs(foo, jobs, bar):
    assert jobs.all(lambda job: job.training_time < 100)
    assert foo + 1 == bar
```

### Passing filters via the CLI
SageTest adds the `--sagetest-filters` option to the pytests CLI. `--sagetest-filters` takes a dictionary of Filter `kwargs`. The matched training jobs are accessible by the tests via the `cli_fixtures`.

Example:
Invoking pytest like this:

```shell
pytest <my-test-file> --sagetest-filters='{<filter-name>:<filter-kwargs>}'
```

Makes the jobs matched by the `<filter-kwargs>` accessible from a test function via the `cli_fixtures` parameter.

```python
# contents of test_<something>.py
def test_jobs_from_cli(cli_fixtures):
    jobs = cli_fixtures["<filter-name>"]
    ...
```

In order to initialize the `cli_fixtures` fixture, `SageTest.init_cli()` needs to be called atleast once in the test file or in a `conftest.py`. 

```python
# conftest.py or test_<something>.py
from sagetest import SageTest
sagetest = SageTest(boto3.Session())
cli = sagetest.init_cli()
```

More examples see [examples/cli/](examples/cli).

### Querying SageMaker from a test

The sagetest object can be made accesible as a fixture by calling the `init_fixture` method of a SageTest object. 

```python
# contents of conftest.py or test_<something>.py
sagetest = SageTest(...)
fixture = sagetest.init_fixture() 
```

This makes the `sagetest_instance` available as fixture for test functions.

```python
# contents of test_<something>.py
def test_smth(sagetest_instance):
    jobs = sagetest_instance.search([Filter(...)])
```

Note that fixtures are cached and that the `sagetest.search` call is not. Thus calling `search` is useful when writing test or debugging but increases the time taken for tests if searches are repeated.


## Working with training jobs
Training jobs are available in tests as objects of the `Job` and `Jobs` classes.

### The Job class
A `Job` is a single training job, common features such as training time and the training job name are available as attributes of this class. The Json which SageMaker uses to 

### The Jobs class
When writing tests using SageTest the training jobs will be returned as the `Jobs` class. 

The `Jobs` class has the following features which simplify writing tests:

* `Jobs.metrics` is a pandas dataframe containing the metrics for all the training jobs.
* `Jobs.all` Apply a function to all items in the `Jobs` object. If all evaluate to `True`, return `True` otherwise this returns `False`.
* `Jobs.where` filter out a subset of the `Job` objects.
