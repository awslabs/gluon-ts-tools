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
import pandas
from sagetest import Filter, SageTest
from sagetest.jobs import Job, Jobs

# create a SageTest sesssion
sagetest = SageTest(
    locals(),
    session=boto3.Session(),
)

# Create a pytest fixture containing SageMaker training jobs
sagetest.fixture(
    fixture_name="reference_job",
    filters=Filter(names=["a training job name"]),
)

# Use fixture
def test_sagetest_fixture(reference_job: Jobs):
    assert isinstance(reference_job.metrics, pandas.DataFrame)


# Decorate with pytest.mark.parametrize populated with SageMaker training jobs
@sagetest.parametrize(
    "jobs",
    [
        Filter(names=["some job name"]),
        Filter(names=["another job name"]),
    ],
)
def test_some_jobs(jobs: Jobs):
    assert len(jobs) == 2
    assert isinstance(jobs[0], Job)
    assert jobs.metrics["abs_error"].mean() < 100
