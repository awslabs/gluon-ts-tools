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

"""Pytest plugin which adds a commandline option to pytest."""


def pytest_addoption(parser):
    """Add --fixtures as option to pytest cli"""

    parser.addoption(
        "--sagetest_fixtures",
        action="store",
        default="{}",
        help="""Dictionary which will be added to the `cli_fixtures` fixture when tests are run. 
        The values of the dictionary will be passed to a Filters object as kwargs and must thus. 
        These filters are then used to query SageMaker.

        Example:

        {\"my_fixture\": {\"names\": [\"my-training-job-name\"]}}
        
        Is accessable in the test file as:

        def my_test(cli_fixtures):
            jobs = cli_fixtures['my_fixture']
        """,
    )
