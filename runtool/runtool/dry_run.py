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

import os
from typing import List

import click
import pandas
import yaml
from beautifultable import BeautifulTable

from runtool.dispatcher import JobConfiguration
from runtool.utils import get_item_from_path


def generate_dry_run_table(
    jobs: List[JobConfiguration], print_data: bool = True
) -> pandas.DataFrame:
    """
    Generate a dry run table summarizing the jobs and optionally print it.

    Returns
    -------
    pandas.DataFrame
        The table as a pandas dataframe
    """
    paths = dict(
        image="AlgorithmSpecification.TrainingImage",
        hyperparameters="HyperParameters",
        output_path="OutputDataConfig.S3OutputPath",
        instance="ResourceConfig.InstanceType",
        job_name="TrainingJobName",
    )

    table_data = []
    for job_definition in jobs:
        row = {
            key: get_item_from_path(job_definition, path)
            for key, path in paths.items()
        }

        row["tags"] = {
            tag["Key"]: tag["Value"] for tag in job_definition["Tags"]
        }
        row["run"] = row["tags"]["run_number"]
        row["datasets"] = [
            get_item_from_path(channel, "DataSource.S3DataSource.S3Uri")
            for channel in job_definition["InputDataConfig"]
        ]

        table_data.append(row)

    table = BeautifulTable(maxwidth=os.get_terminal_size().columns)
    table.columns.header = [
        click.style(key, bold=True) for key in table_data[0].keys()
    ]
    for item in table_data:
        table.rows.append(
            yaml.dump(val).rstrip("...") for val in item.values()
        )

    table.columns.alignment = BeautifulTable.ALIGN_LEFT
    if print_data:
        print(table)
        print(f"total number of jobs: {len(table.rows)}")
    return table_data
