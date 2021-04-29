import json
from pathlib import Path, PurePath
from urllib.parse import urlparse

import click
from gtstlib import Resource, TrainingJob, env
from toolz import valmap

from ._base import main, Arn


def get_data_channels(description):
    return {
        channel["ChannelName"]: channel["DataSource"]["S3DataSource"]["S3Uri"]
        for channel in description["InputDataConfig"]
    }


def download_files(bucket, prefix, destination):
    for key_object in bucket.objects.filter(Prefix=prefix.lstrip("/")):
        path = PurePath(key_object.key)

        bucket.download_file(str(path), str(destination / path.name))


@main.command()
@click.option("--arn", type=Arn)
@click.argument("destination", type=click.Path())
@click.option("-p", "--profile", default=None)
def scaffold(arn, destination, profile):
    """Replicate a TrainingJobs folder structure locally."""
    if arn:
        resource = Resource.from_profile(profile, arn)
        assert type(resource) == TrainingJob, "Only TrainingJobs can be used"
        hyperparameters = resource._description["HyperParameters"]
        channels = get_data_channels(resource._description)
    else:
        hyperparameters = {}
        channels = {"train": None, "test": None}

    destination = Path(destination)
    make_config(destination, hyperparameters, channels)
    download_data(destination, channels)


def make_config(destination, hyperparameters, channels):
    config = destination / "input" / "config"
    config.mkdir(parents=True, exist_ok=True)

    # hyperparameters
    hyperparameters = valmap(str, hyperparameters)
    with open(config / "hyperparameters.json", "w") as hp_file:
        json.dump(hyperparameters, hp_file)

    # inputdataconfig
    input_data_config = {
        channel: {"ContentType": "auto"} for channel in channels
    }
    with open(config / "inputdataconfig.json", "w") as idc_file:
        json.dump(input_data_config, idc_file)


def download_data(destination, channels):
    data = destination / "input" / "data"
    data.mkdir(parents=True, exist_ok=True)

    for channel_name, s3path in channels.items():
        channel_path = data / channel_name
        channel_path.mkdir(exist_ok=True)

        if s3path is not None:
            download_files(s3path, channel_path)


def download_files(s3path, channel_path):
    s3 = env.boto_session.resource("s3")

    url = urlparse(s3path)
    bucket = s3.Bucket(url.netloc)
    path = url.path.lstrip("/")

    for path in bucket.objects.filter(Prefix=path):
        name = PurePath(path.key).name

        bucket.download_file(path.key, str(channel_path / name))
