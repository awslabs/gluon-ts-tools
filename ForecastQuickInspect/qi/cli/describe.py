import click
import rich
from gtstlib import Resource

from ._base import main, Arn


@main.command()
@click.argument("arn", type=Arn)
@click.option("-p", "--profile", default=None)
def describe(arn, profile):
    """Get SageMaker resources description with `rich` terminal formatting."""
    resource = Resource.from_profile(profile, arn)
    rich.print(resource.description())
