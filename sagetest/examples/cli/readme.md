# Using SageTest via the pytest cli
One can populate fixtures in pytest with SageMaker training jobs by using the `--sagetest-fixtures` option when running pytest.

```bash
pytest <path> --sagetest-fixtures <filters>
```

The `<filters>` argument is a dictionary mapping a name to `sagetest.Filters` kwargs. I.e. valid `<filters>` have the following structure:

```json
"{'<fixture_name>': '<kwargs for `sagetest.Filter`>'}"
```

Training jobs that match the supplied filters are then accessible via the `cli_fixtures` fixture in tests. 

## Example
Running the below command makes jobs with the name `job-name` available for tests.

```bash
pytest test_cli_example.py --sagetest-fixtures '{"my_jobs": {"names": ["job-name"]}}'
```

In the python file where your tests are defined, you can then request the `cli_fixtures` fixture which contains the matched training jobs under the key you supplied. In this case the key is `my_jobs`.

```python
#contents of the test file
from sagetest import SageTest
import boto3

sagetest = SageTest(boto3.Session())  # can be in conftest.py
cli = sagetest.init_cli()

def my_test(cli_fixtures):
    jobs = cli_fixtures['my_jobs']
    # do some tests on the matched jobs
```

An implementation of this example can be found in the `run_test.sh` and the `test_cli_example.py` files.
