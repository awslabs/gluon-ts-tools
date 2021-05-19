"""
This test file should be tested via the below command to make the cli fixture testable.

pytest test_builtin_fixtures.py --sagetest-fixtures='{"test_fixture": {"names": ["test-name"]}}'
"""
from unittest.mock import MagicMock

from sagetest import SageTest
from sagetest.jobs import Jobs
from sagetest.search import Filter

sagetest = SageTest(None)  # None due to mocking
sagetest.search = MagicMock()
sagetest.search.return_value = Jobs()
sagetest_fixture = sagetest.init_fixture()
sagetest_cli_fixture = sagetest.init_cli()


def test_sagetest_cli(cli_fixtures):
    """Ensure that commandline arguments are properly converted to Jobs objects."""
    assert isinstance(cli_fixtures, dict)
    assert isinstance(cli_fixtures.get("test_fixture"), Jobs)
    sagetest.search.assert_called_once_with(Filter(names=["test-name"]))


def test_sagetest_instance(sagetest_instance):
    """Ensure that sagetest is accessible via a fixture."""
    assert isinstance(sagetest_instance, SageTest)
    assert isinstance(sagetest_instance.search(None), Jobs)
