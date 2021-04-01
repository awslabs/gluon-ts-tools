import os
from typing import List

import click
import pandas
import yaml
from beautifultable import BeautifulTable

from runtool.utils import get_item_from_path
from runtool.dispatcher import JobConfiguration


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
