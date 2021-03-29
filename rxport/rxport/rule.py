import re
from enum import Enum
from typing import Any, Union, Optional, Dict

from pydantic import BaseModel, Field
from toolz import valmap


class Aggregation(str, Enum):
    unique = "unique"
    first = "first"
    last = "last"
    final = "final"
    id = "id"
    mean = "mean"
    sum = "sum"
    min = "min"
    max = "max"
    count = "count"

    def __call__(self, xs):
        from statistics import mean
        from toolz import first, last, identity

        fn = {
            Aggregation.unique: first,
            Aggregation.first: first,
            Aggregation.last: last,
            Aggregation.final: last,
            Aggregation.id: identity,
            Aggregation.mean: mean,
            Aggregation.sum: sum,
            Aggregation.min: min,
            Aggregation.max: max,
            Aggregation.count: len,
        }[self]

        return fn(xs)


class Type(str, Enum):
    json = "json"
    literal_eval = "literal_eval"
    float = "float"
    int = "int"
    str = "str"

    def eval(self, value):
        import ast
        import json

        fn = {
            Type.json: json.loads,
            Type.literal_eval: ast.literal_eval,
            Type.float: float,
            Type.int: int,
            Type.str: str,
        }[self]

        return fn(value)


class GroupPattern:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, val):
        if isinstance(val, cls):
            rx = val.rx
        else:
            rx = val

        if not isinstance(rx, re.Pattern):
            rx = re.compile(rx)

        assert (
            rx.groups == 1
        ), f"Pattern needs to have exactly one matching group, got {rx.groups}."

        return cls(rx)

    def __init__(self, rx: re.Pattern) -> None:
        self.rx = rx

    def __call__(self, message: str) -> Optional[str]:
        for match in self.rx.finditer(message):
            return match.group(1)


class RxName(BaseModel):
    r"""
    (\w) = bar
    """
    rx: GroupPattern

    def apply(self, message):
        return self.rx(message)


class RxValue(BaseModel):
    rx: GroupPattern
    type: Type = Type.str

    def apply(self, message) -> Optional[Any]:
        value = self.rx(message)

        if value is not None:
            return self.type.eval(value)


class MetaField(BaseModel):
    rx: Optional[GroupPattern]
    name: Optional[str]
    type: Type = Type.str

    def apply(self, message: str) -> Optional[Any]:
        value = self.rx(message)

        if value is not None:
            return self.type.eval(value)


Name = Union[str, RxName]


def get_name(name: Name, message) -> Optional[str]:
    if isinstance(name, str):
        return name

    return name.eval(message)


class Entry(BaseModel):
    rule: str
    name: str
    value: Any
    # group: Optional[str]
    meta: Dict = {}


class Rule(BaseModel):
    rule: str
    name: Name
    value: RxValue
    aggr: Aggregation = Aggregation.id
    meta: Dict[str, Union[str, MetaField]] = {}

    def apply(self, message):
        name = get_name(self.name, message)
        if name is None:
            return

        value = self.value.apply(message)
        if value is None:
            return

        return Entry(
            rule=self.rule, name=name, value=value, meta=self.get_meta(message)
        )

    def get_meta(self, message):
        return valmap(
            lambda meta: meta.apply(message) if isinstance(meta, MetaField) else meta,
            self.meta,
        )
