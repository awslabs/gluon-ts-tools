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

import boto3
from sagetest import Filter, SageTest
from sagetest.jobs import Jobs

sagetest = SageTest(boto3.Session())


@sagetest.fixture()  # parameters passed to @pytest.fixture decorator
def reference_job():
    return Filter(names=["<a training job name>"])


# Use fixture
def test_sagetest_fixture(reference_job: Jobs):
    assert reference_job.metrics["abs_error"].mean() < 100


# parametrize with SageMaker training jobs
@sagetest.parametrize(
    "jobs",
    [
        Filter(names=["<some job name>"]),
        Filter(names=["<another job name>"]),
    ],
)
def test_some_jobs(jobs: Jobs):
    # do some tests on the matched jobs below
    assert jobs.metrics["MASE"].mean() < 1
    assert jobs.all(lambda job: job.training_time < 60)
    assert len(jobs) == 1

    # apply additional filtering if needed
    subset = jobs.where(lambda job: "<my_tag>" in job.tags)
