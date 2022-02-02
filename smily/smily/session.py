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

from dataclasses import dataclass
from typing import Optional

from smily.lib import Resource, TrainingJob


@dataclass
class Session:
    session: boto3.Session
    region: Optional[str] = None

    def _from_arn(self, arn):
        sagemaker = self.session.client("sagemaker", region_name=arn.region)
        logs = self.session.client("logs", region_name=arn.region)

        return Resource.from_arn(arn, sagemaker=sagemaker, cw_logs=logs)

    def _from_name(self, cls, name):
        sagemaker = self.session.client("sagemaker", region_name=self.region)
        logs = self.session.client("logs", region_name=self.region)

        return cls.from_name(name, sagemaker=sagemaker, cw_logs=logs)

    def _from(self, cls, name, arn):
        if arn is not None:
            return self._from_arn(arn)

        if name is not None:
            return self._from_name(cls, name)

        raise ValueError("Either `name` or `arn` need to be passed.")

    def processing_job(self, *, name=None, arn=None):
        self._from(ProcessingJob, name, arn)

    def training_job(self, *, name=None, arn=None):
        self._from(TrainingJob, name, arn)

    def transform_job(self, *, name=None, arn=None):
        self._from(TransformJob, name, arn)

    def hyper_parameter_tuning_job(self, *, name=None, arn=None):
        self._from(HyperParameterTuningJob, name, arn)

    def endpoint(self, *, name=None, arn=None):
        self._from(Endpoint, name, arn)

    def notebook_instance(self, *, name=None, arn=None):
        self._from(NotebookInstance, name, arn)
