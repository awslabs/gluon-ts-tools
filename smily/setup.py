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

from setuptools import setup, find_packages

setup(
    name="smily",
    author="Amazon",
    version="0.0.4",
    author_email="gluon-ts-dev@amazon.com",
    maintainer_email="gluon-ts-dev@amazon.com",
    packages=find_packages("."),
    install_requires=[
        "boto3",
        "toolz",
        "pydantic",
    ],
    extras_require={"cli": ["click", "rich"]},
    entry_points={
        "console_scripts": ["smily=smily.__main__:main"],
    },
)
