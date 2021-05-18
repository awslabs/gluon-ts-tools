# Using SageTest via the pytest cli
One can populate fixtures in pytest with SageMaker training jobs by using the `--sagetest-fixtures` option as below.

```bash
pytest <path> --sagetest-fixtures <filters>
```

The `<filters>` argument is a dictionary mapping a name to `sagetest.Filters` kwargs. I.e. valid `<filters>` have the following structure:

```json
"{'<fixture_name>': '<kwargs for `sagetest.Filter`>'}"
```

Training jobs which match the filters are then accessible via the `cli_fixtures` fixture during tests. 

## Example
An end to end example of how SageTest can be used to via the cli is shown below. Note that the below material is implemented in the current directory as well in the `conftest.py`, `run_test.sh` and the `test_example.py` files. 

```bash
pytest test_my_file.py --sagetest-fixtures '{"my_jobs": {"names": ["job-name"]}}'
```

In the python file you wish to test, you can then request the `cli_fixtures` parameters which will include the matched training jobs.

```python
#contents of the test file
def my_test(cli_fixtures):
    jobs = cli_fixtures['my_jobs']
    # do some tests on the matched jobs
```

### conftest.py
In the conftest.py you should initialize SageTest as below. 

```python
# contents of conftest.py
sagetest = SageTest(locals(), session=boto3.Session())
```

Initializing SageTest can also be done in the test files.
