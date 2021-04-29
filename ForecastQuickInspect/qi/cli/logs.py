import click
from gtstlib import Resource

from ._base import main, Arn, AliasedGroup


@main.group(cls=AliasedGroup)
def logs():
    """Interact with cloudwatch logs of a training-job, processing-job,
    endpoint, hyperparameter-tuning-job, notebook-instance or a
    transform-job."""
    pass


@logs.command()
@click.argument("arn", required=True, type=Arn)
@click.option("-n", type=int, default=10)
@click.option("-p", "--profile", default=None)
def head(arn, n, profile):
    """Show beginning of the logs."""
    resource = Resource.from_profile(profile, arn)
    for log in resource.logs:
        click.secho(log.stream_name, bold=True, color="blue", err=True)
        for line in log.head(n=n):
            click.echo(line)
        click.echo()


@logs.command()
@click.argument("arn", required=True, type=Arn)
@click.option("-f", "follow", is_flag=True)
@click.option("-i", "--interval", default=10)
@click.option("-p", "--profile", default=None)
def tail(arn, n, follow, interval, profile):
    """Show end of logs."""
    resource = Resource.from_profile(profile, arn)
    for log in resource.logs:
        click.secho(log.stream_name, bold=True, color="blue", err=True)
        if follow:
            lines = log.follow(limit=n, start_at_top=False, interval=interval)
        else:
            lines = log.tail(n)

        for line in lines:
            click.echo(line)
        click.echo()


@logs.command()
@click.argument("arn", required=True, type=Arn)
@click.option("-f", "follow", is_flag=True)
@click.option("-i", "--interval", default=10)
@click.option("-p", "--profile", default=None)
def cat(arn, follow, interval, profile):
    """Show full logs."""
    resource = Resource.from_profile(profile, arn)
    for log in resource.logs:
        click.secho(log.stream_name, bold=True, color="blue", err=True)

        if follow:
            lines = log.follow(interval=interval)
        else:
            lines = log.cat()

        for line in lines:
            click.echo(line)
        click.echo()


@logs.command()
@click.argument("arn", required=True, type=Arn)
@click.option("--expression", "-e", required=True)
@click.option("-p", "--profile", default=None)
def filter(arn, expression, profile):
    """Filter logs according to an expression."""
    resource = Resource.from_profile(profile, arn)
    for name, logfilterevents in resource.logfilter.filter(expression).items():
        click.secho(name, bold=True, color="blue", err=True)
        for evt in logfilterevents:
            click.secho(evt.message)
        click.echo()
