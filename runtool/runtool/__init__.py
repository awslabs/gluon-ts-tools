import runtool.config_parser as config_parser
import runtool.dryrun as dryrun
import runtool.runtool as runtool
from runtool.local_runner import run_training_on_local_machine
from runtool.runtool import Client, expand_experiments


def parse_config(data):
    return config_parser.apply_transformations(data)


def load_config(data):
    return runtool.load_config(data)


def expand_experiment(data):
    return runtool.expand(data)
