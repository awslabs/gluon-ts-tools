import click
import pandas as pd
import yaml
from beautifultable import BeautifulTable


def generate_dry_run_table(sagemaker_json: dict, print_table: bool):
    def get(data, path):
        for key in path.split("."):
            data = data[key]
        return data

    table_data_paths = {
        "image": "AlgorithmSpecification.TrainingImage",
        "hyperparameters": "HyperParameters",
        "output_path": "OutputDataConfig.S3OutputPath",
        "instance": "ResourceConfig.InstanceType",
        "job_name": "TrainingJobName",
    }

    table_data = []
    for job_definition in sagemaker_json:
        row = {}
        for key, path in table_data_paths.items():
            row[key] = get(job_definition, path)

        row["tags"] = {
            tag["Key"]: tag["Value"] for tag in job_definition["Tags"]
        }
        row["run"] = row["tags"]["run_number"]
        row["datasets"] = [
            get(channel, "DataSource.S3DataSource.S3Uri")
            for channel in job_definition["InputDataConfig"]
        ]

        table_data.append(row)

    table = BeautifulTable(maxwidth=230)
    table.columns.header = [
        click.style(key, bold=True) for key in table_data[0].keys()
    ]
    for item in table_data:
        table.rows.append(
            yaml.dump(val).rstrip("...") for val in item.values()
        )

    table.columns.alignment = BeautifulTable.ALIGN_LEFT
    if print_table:
        print(table)
        print(f"total number of jobs: {len(table.rows)}")
    return pd.DataFrame(table_data)
