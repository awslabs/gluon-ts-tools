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

import pandas as pd
import pytest
from sagetest.jobs import Job, Jobs

from jsons import JOB_JSON_1, JOB_JSON_2

JOB_1 = Job(
    metrics={"MASE": 0.9552038311958313, "abs_error": 12105318.0},
    training_time=801,
    tags={
        "config_id": "default_benchmark_name/1234",
        "dataset_id": "electricity",
    },
    hyperparameters={
        "distr_output": '{"__kind__": "instance","class": "gluonts.mx.distribution.NegativeBinomialOutput","args": [],"kwargs": {}}',
        "forecaster_name": "gluonts.model.deepar.DeepAREstimator",
        "freq": "1H",
        "prediction_length": "24",
    },
    source=JOB_JSON_1,
    name="dummy-job-1",
)

JOB_2 = Job(
    metrics={"MASE": 1, "abs_error": 100},
    training_time=10,
    tags={"config_id": "dummy", "dataset_id": "dummy2"},
    hyperparameters={"prediction_length": "24"},
    source=JOB_JSON_2,
    name="dummy-job-2",
)


@pytest.fixture
def jobs():
    yield Jobs([JOB_1, JOB_2])


def test_job_from_json():
    assert Job.from_json(JOB_JSON_1) == JOB_1
    assert Job.from_json(JOB_JSON_2) == JOB_2


def test_jobs(jobs):
    assert jobs[0] == JOB_1
    assert jobs[1] == JOB_2
    assert jobs == Jobs.from_json_list([JOB_JSON_1, JOB_JSON_2])
    assert jobs == Jobs([JOB_1, JOB_2])


def test_jobs_where(jobs):
    assert jobs.where(lambda job: job.training_time == 10) == Jobs([JOB_2])


def test_jobs_all(jobs):
    assert jobs.all(lambda job: job.metrics["MASE"] <= 1)


def test_jobs_metrics(jobs):
    assert isinstance(jobs.metrics, pd.DataFrame)
    assert jobs.metrics["abs_error"].mean() == 6052709.0
    assert jobs.metrics["MASE"].mean() == 0.9776019155979156

    # ensure that pop updates the metrics dataframe correctly
    assert jobs.pop(0) == JOB_1
    assert jobs.metrics["abs_error"].mean() == 100.0
    assert jobs.metrics["MASE"].mean() == 1.0
