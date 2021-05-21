# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

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
