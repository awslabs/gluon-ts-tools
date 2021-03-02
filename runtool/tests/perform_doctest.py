from doctest import testmod

from runtool import (
    datatypes,
    recurse_config,
    runtool,
    transformations,
    transformer,
    utils,
)

for module in (
    datatypes,
    recurse_config,
    runtool,
    transformations,
    transformer,
    utils,
):
    testmod(module)
