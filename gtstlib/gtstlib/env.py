import boto3

# TODO: we could use it from gluon-ts, but this would add a major dependency
from ._settings import Settings, Dependency


def sagemaker_client(boto_session):
    return boto_session.client("sagemaker")


def logs_client(boto_session):
    return boto_session.client("logs")


class Env(Settings):
    boto_session: boto3.Session
    sagemaker: Dependency = sagemaker_client
    cw_logs: Dependency = logs_client


env = Env()
