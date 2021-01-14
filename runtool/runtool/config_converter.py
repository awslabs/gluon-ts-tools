from functools import singledispatch
from typing import Any, Union, List, Dict
from runtool.datatypes import (
    Algorithm,
    Algorithms,
    Dataset,
    Datasets,
    Generics,
    Versions,
)


@singledispatch
def infer_type(node: Any) -> Any:
    """
    Base case, of single dispatch converting nodes in JSON
    structure to Algorithms, Datasets or Generics
    """
    return node


@infer_type.register
def infer_type_list(node: list) -> Union[Algorithms, Datasets, Generics, Any]:
    if len(node) == 0:
        return Generics(node)
    elif Algorithms.verify(node):
        return Algorithms(node)
    elif Datasets.verify(node):
        return Datasets(node)
    else:
        try:
            return Generics(node)
        except:
            return node


@infer_type.register
def infer_type_dict(node: dict) -> Union[Algorithm, Dataset, Generics, Any]:
    if Algorithm.verify(node):
        return Algorithm(node)
    elif Dataset.verify(node):
        return Dataset(node)
    else:
        try:
            return Generics(node)
        except:
            return node


@singledispatch
def convert_to_types(data: Any) -> Any:
    """
    Base case of singledispatch which converts a
    JSON-like structure to Algorithms, Datasets and Generics
    """
    return data


@convert_to_types.register
def convert_to_types_list(data: list) -> List[Any]:
    return [infer_type(item) for item in data]


@convert_to_types.register
def convert_to_types_dict(data: dict) -> Dict:
    return {key: infer_type(value) for key, value in data.items()}


@convert_to_types.register
def convert_to_types_versions(data: Versions) -> Versions:
    return Versions([infer_type(item) for item in data.versions])
