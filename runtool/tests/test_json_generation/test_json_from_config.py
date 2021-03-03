import yaml
from runtool.runtool import load_config, transform_config
from runtool.runtool import Client, generate_sagemaker_json
from pathlib import Path


def compare(testname: str):
    """
    This method uses the `testname` parameter to locate two files
    containing testdata. An `Experiment` object is then generated
    and passed to the `generate_sagemaker_json` method.
    The resulting Json is then compared to reference data.

    The data which this method uses is loaded from the `test_data` directory
    of the current folder.
    """
    path = Path(__file__).parent / "test_data" / testname
    config = load_config(path / "source.yml")

    with open(path / "expected.yml") as expected:
        assert (
            list(
                generate_sagemaker_json(
                    config.algorithms * config.datasets,
                    runs=1,
                    experiment_name="dummy_name",
                    job_name_expression="'mocked_name'",
                    tags={"repeated_runs_group_id": "mocked_value"},
                    creation_time="2021-02-23-14-36-39",
                    bucket="dummy_bucket",
                    role="dummy_role",
                )
            )
            == yaml.safe_load(expected)
        )


def test_minimum():
    """
    Tests a minimum viable config file containing one algorithm
    and one dataset
    """
    compare("minimum")


def test_large():
    """
    Tests a large config file containing 6 algorithms and 5 datasets
    thus generating a total of 30 training jobs.
    """
    compare("large")
