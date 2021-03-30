# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

from functools import singledispatch
from pathlib import Path
from typing import Any, Dict, Iterable, Union
from collections import defaultdict

import yaml
from toolz import valmap

from runtool.datatypes import (
    Algorithm,
    Algorithms,
    Dataset,
    Datasets,
    DotDict,
    Experiment,
    Experiments,
)
from runtool.recurse_config import Versions
from runtool.transformer import apply_transformations
from functools import singledispatch


@singledispatch
def infer_type(node):
    """
    Basecase for infer_type, Any node which is not handled by
    another singledispatch function should be returned unaltered.
    """
    return node


@infer_type.register
def infer_type_list(
    node: list,
) -> Union[Algorithms, Datasets, Experiments, list]:
    """
    infer_type_list converts a list into an instance
    of one of the following classes.

    - Algorithms
    - Datasets
    - Experiments

    Example:

    >>> algorithm = {
    ...     "image": "image_name",
    ...     "instance": "ml.m5.2xlarge",
    ...     "hyperparameters": {},
    ... }
    >>> isinstance(infer_type([algorithm]), Algorithms)
    True

    >>> dataset = {
    ...     "path": {
    ...         "train": "some path"
    ...     },
    ...     "meta": {},
    ... }
    >>> isinstance(infer_type([dataset]), Datasets)
    True

    >>> experiment = {
    ...     "dataset": dataset,
    ...     "algorithm": algorithm,
    ... }
    >>> isinstance(infer_type([experiment]), Experiments)
    True

    If the node does not match the structure required for either
    Algorithms, Datasets or Experiments, the node is returned unaltered.

    >>> infer_type([]) == []
    True

    >>> infer_type([algorithm, dataset]) == [algorithm, dataset]
    True

    """
    for class_ in (Algorithms, Datasets, Experiments):
        if class_.verify(node):
            return class_(node)
    return node


@infer_type.register
def infer_type_dict(node: dict) -> Union[Algorithm, Dataset, Experiment, dict]:
    """
    infer_type_dict converts a dict into an instance
    of one of the following classes.

    - Algorithm
    - Dataset
    - Experiment

    Example:
    >>> algorithm = {
    ...     "image": "image_name",
    ...     "instance": "ml.m5.2xlarge",
    ...     "hyperparameters": {},
    ... }
    >>> isinstance(infer_type(algorithm), Algorithm)
    True

    >>> dataset = {
    ...     "path": {
    ...         "train": "some path"
    ...     },
    ...     "meta": {},
    ... }
    >>> isinstance(infer_type(dataset), Dataset)
    True

    >>> experiment = {
    ...     "dataset": dataset,
    ...     "algorithm": algorithm,
    ... }
    >>> isinstance(infer_type(experiment), Experiment)
    True

    If the node matches multiple classes, the first match will be returned.
    An example of this is when a dictionary contains both a valid algorithm
    and a valid dataset. See below example.

    >>> isinstance(infer_type(dict(**algorithm, **dataset)), Algorithm)
    True

    If the node does not match the structure required for either
    Algorithm, Dataset or Experiment, the node is returned unaltered.
    >>> infer_type({}) == {}
    True
    """
    for class_ in (Algorithm, Dataset, Experiment):
        if class_.verify(node):
            return class_(node)
    return node


def infer_types(data: dict) -> dict:
    return valmap(infer_type, data)


def generate_versions(data: Iterable[dict]) -> Dict[Any, Versions]:
    """
    Converts an Iterable collection of dictionaries to a single dictionary
    where each value is a `runtool.datatypes.Versions` object.
    If two dictionaries has the same keys, their values are appended to the
    `Versions` object.

    example:

    >>> generate_versions([{"a": 1}])
    {'a': 1}

    >>> generate_versions([{"a": 1}, {"a": 2}])
    {'a': Versions([1, 2])}

    >>> generate_versions(
    ...     [
    ...         {"a":1},
    ...         {"a":2,"b":3},
    ...     ]
    ... )
    {'a': Versions([1, 2]), 'b': 3}
    """

    # creates a new Versions object for any new keys and appends
    # the value to the created Versions object
    result = defaultdict(Versions)
    for dct in data:
        for key, value in dct.items():
            result[key].append(value)
    return dict(result)


def load_config(path: Union[str, Path]) -> DotDict:
    """
    Loads a yaml file from the provided path and calls converts it
    to a dictionary and then calls `transform_config` on the data.
    """
    with open(path) as config_file:
        return transform_config(yaml.safe_load(config_file))


def transform_config(config: dict) -> DotDict:
    """
    This function applies a series of transformations to a runtool config
    before converting it into a DotDict. The config is transformed through
    the following procedure:

    First, the config will have any $ statements such as $each or $eval
    resolved using the `runtool.transformer.apply_transformations`
    function on the config.

    i.e.

    >>> transformed = apply_transformations(
    ...     {
    ...         "my_algorithm": {"image": {"$each": ["1", "2"]}, "instance":'...'},
    ...     }
    ... )
    >>> transformed == [
    ...     {'my_algorithm': {'image': '1', 'instance': '...'}},
    ...     {'my_algorithm': {'image': '2', 'instance': '...'}}
    ... ]
    True

    Thereafter, each dictionary in the list returned by `apply_transformations`
    will be converted to a suitable datatype by calling the
    `runtool.infer_type.infer_types` method.
    In the example below, `my_algorithm` is converted to a
    `runtool.datatypes.Algorithm` object:

    >>> inferred = [infer_types(item) for item in transformed]
    >>> inferred == [
    ...     {'my_algorithm': Algorithm({'image': '1', 'instance': '...'})},
    ...     {'my_algorithm': Algorithm({'image': '2', 'instance': '...'})}
    ... ]
    True

    The list of dicts which we now have is then converted into a dict
    of Versions objects via the `generate_versions` function.

    >>> as_versions = generate_versions(inferred)
    >>> as_versions == {
    ...     "my_algorithm": Versions(
    ...         [
    ...             Algorithm({"image": "1", "instance": "..."}),
    ...             Algorithm({"image": "2", "instance": "..."})
    ...         ]
    ...     )
    ... }
    True

    Finally, the dict is converted to a DotDict and returned.
    """
    return DotDict(
        generate_versions(map(infer_types, apply_transformations(config)))
    )
