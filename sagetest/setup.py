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

from setuptools import find_packages, setup

setup(
    name="sagetest",
    version="0.1.0",
    author="Amazon",
    packages=find_packages("./sagetest"),
    description="Sagetest package for applying tests to sagemaker training jobs",
    include_package_data=True,
    install_requires=[
        "PyYAML",
        "pydantic",
        "toolz",
        "pytest",
        "Click",
        "pyyaml",
        "pandas",
    ],
    entry_points={
        "console_scripts": ["sagetest = sagetest.cli:cli"],
        "pytest11": ["name_of_plugin = sagetest.plugin.conftest"],
    },
)
