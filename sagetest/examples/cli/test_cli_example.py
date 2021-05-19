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

from sagetest import SageTest
import boto3

sagetest = SageTest(session=boto3.Session())  # can be in conftest.py

# the cli_fixtures fixture contains jobs matched by --sagetest-fixtures option
def test_my_param(cli_fixtures):
    jobs = cli_fixtures["my_jobs"]

    # do some tests on the matched jobs below
    assert jobs.metrics["MASE"].mean() < 1
    assert jobs.all(lambda job: job.training_time < 60)
    assert len(jobs) == 5
