import inspect
import os
from pathlib import Path

import runtool as entrypoint


def get_module_dir():
    return str(os.path.dirname(inspect.getfile(entrypoint.__main__)))


def get_cache_dir():
    return str(Path.home() / "gluonts-run-tool")


def get_stdlib_path():
    return get_module_dir() + "/defaults/stdlib.yml"


def get_user_defaults_path():
    return get_cache_dir() + "/runtool/defaults/default.yml"


def get_cloudformation_path():
    return get_module_dir() + "/cloudformation.yml"
