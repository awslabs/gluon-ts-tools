import webbrowser

import click
from gtstlib import Resource

from ._base import main, Arn

federate_help = (
    "Generate an isengard ferderate link, which logs into the account."
)
print_help = "Print link instead of opening it in the browser."


@main.command()
@click.argument("arn", required=True, type=Arn)
@click.option("--print", "-p", "print_", is_flag=True, help=print_help)
def open(arn, print_):
    """
    Open a SageMaker Resource in the browser:

        qi open arn:aws:sagemaker:us-east-1:123456789012:training-job/job-name

    The -p/--print option just prints the link, instead of opening it.
    """
    ResourceKind = Resource.class_for_arn(arn)

    destination = (
        f"sagemaker/home?region={arn.region}"
        f"#/{ResourceKind.url_prefix}/{arn.resource_id}"
    )

    url = f"https://{arn.region}.console.aws.amazon.com/{destination}"

    if print_:
        click.echo(url)
    else:
        webbrowser.open(url)
