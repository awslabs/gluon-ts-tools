from runtool import transformer
from runtool.runtool import load_config, Client


def parse(data):
    return transformer.apply_transformations(data)
