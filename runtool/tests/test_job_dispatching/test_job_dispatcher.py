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

import json
from pathlib import Path
from unittest.mock import Mock, patch

import botocore
import pytest
from runtool.dispatcher import JobDispatcher, group_by_instance_type

RESPONSE = {
    "TrainingJobArn": "arn:aws:sagemaker:eu-west-1:012345678901:training-job/test-60a848663fa1",
    "ResponseMetadata": {
        "RequestId": "00924112-abcd-4aed-6d4d-28190dba0b68",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
            "x-amzn-requestid": "00924112-abcd-4aed-6d4d-28190dba0b68",
            "content-type": "application/x-amz-json-1.1",
            "content-length": "92",
            "date": "Tue, 16 Mar 2021 11:19:06 GMT",
        },
        "RetryAttempts": 0,
    },
}


def load_file(name):
    path = Path(__file__).parent / "test_data" / f"{name}.json"
    with open(path) as file_pointer:
        return json.load(file_pointer)


def test_group_by_instance():
    dispatcher = JobDispatcher(None)
    job = lambda instance, name: {
        "ResourceConfig": {"InstanceType": instance},
        "name": name,
    }
    assert group_by_instance_type([job(1, 1), job(2, 2), job(2, 3)]) == [
        [job(1, 1)],
        [job(2, 2), job(2, 3)],
    ]


def client_side_effects(behaviour: list):
    """
    Emulates the behaviour or a `boto3.Sagemaker.client` for
    mocking purposes. The return value of this function is to
    be used as a `unittest.mock().return_value`.

    Takes a list of responses which will happen in sequence from
    last to first.

    If an item in the list is the string "busy", a
    `ResourceLimitExceeded` exception is triggered.

    If an item in the list is the string "throttle", a
    `ResourceLimitExceeded` exception is triggered.

    Otherwise the item will be returned.

    >>> side_effects = client_side_effects([{}, "throttle", "busy"])
    >>> side_effects()
    Traceback (most recent call last):
        ...
    botocore.exceptions.ClientError: An error occurred (ResourceLimitExceeded) when calling the  operation: Unknown
    >>> side_effects()
    Traceback (most recent call last):
        ...
    botocore.exceptions.ClientError: An error occurred (ThrottlingException) when calling the  operation: Unknown
    >>> side_effects()
    {}
    """

    def client_side_effect(*args, **kwargs):
        current_result = behaviour.pop()
        if current_result == "busy":
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "ResourceLimitExceeded"}}, ""
            )
        if current_result == "throttle":
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "ThrottlingException"}}, ""
            )
        return current_result

    return client_side_effect


def run_dispatch(responses, file_name, expected=None):
    client = Mock()
    client.create_training_job.side_effect = client_side_effects(responses)
    dispatcher = JobDispatcher(client)
    assert dispatcher.dispatch(load_file(file_name)) == expected
    return client


@patch.object(JobDispatcher, "timeout_with_printer")
@patch("time.sleep", return_value=None)
def test_dispatch_success(patched_sleep, mock_timeout_with_printer):
    client = run_dispatch(
        [RESPONSE] * 2,
        "two_trainingjobs",
        {
            "test-106f177b0569": RESPONSE,
            "test-823eea803d1e": RESPONSE,
        },
    )
    assert client.create_training_job.call_count == 2
    assert mock_timeout_with_printer.call_count == 0


@patch.object(JobDispatcher, "timeout_with_printer")
@patch("time.sleep", return_value=None)
def test_dispatch_resources_busy_and_throttled(
    patched_sleep, mock_timeout_with_printer
):
    client = run_dispatch(
        [RESPONSE, "throttle", "busy", RESPONSE],
        "two_trainingjobs",
        {
            "test-106f177b0569": RESPONSE,
            "test-823eea803d1e": RESPONSE,
        },
    )
    assert client.create_training_job.call_count == 4
    assert mock_timeout_with_printer.call_count == 2


@patch.object(JobDispatcher, "timeout_with_printer")
@patch("time.sleep", return_value=None)
def test_dispatch_retry_limit_reached(
    patched_sleep, mock_timeout_with_printer
):
    with pytest.raises(botocore.exceptions.ClientError):
        # default of 10 retries, thus 11 retries should cause exception
        run_dispatch(["throttle"] * 11, "two_trainingjobs")
