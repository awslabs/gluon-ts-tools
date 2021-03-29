import ast
import json
from operator import attrgetter
from typing import Any, Union, Pattern, Optional, Callable, List

from pydantic import BaseModel, Field

from toolz import identity, first, last
from toolz.curried import groupby, valmap


def mean(xs):
    return sum(xs) / len(xs)


conversion_types = {
    "json": json.loads,
    "literal_eval": ast.literal_eval,
    "float": float,
    "int": int,
    "str": str,
}

aggr_fns = {
    # TODO: instead of `unique`, we could use `any`
    "unique": first,
    "first": first,
    "last": last,
    "final": last,
    "id": identity,
    "mean": mean,
    "sum": sum,
    "min": min,
    "max": max,
    "count": len,
}


class RegexKey(BaseModel):
    rx: Pattern

    def apply(self, message):
        matches = list(self.rx.finditer(message))
        if matches:
            match = matches[0]
            groups = match.groups()
            if len(groups) == 1:
                return groups[0]

        return None


class RegexField(BaseModel):
    rx: Optional[Pattern]
    type: str = "str"
    name: Optional[str]

    def convert(self, value):
        return conversion_types[self.type](value)

    def apply(self, message):
        value = self.apply_rx(message)

        if value is None:
            return None

        value = self.convert(value)

        return value

    def apply_rx(self, message):
        if self.rx is None:
            return message

        matches = list(self.rx.finditer(message))
        if matches:
            match = matches[0]
            groups = match.groups()
            if len(groups) == 1:
                return groups[0]

        return None


class XField(RegexField):
    enumerate: bool = False
    start: int = 0


class X(BaseModel):
    name: str
    value: Any


class Entry(BaseModel):
    name: str
    value: Any
    x: Optional[Any]
    group: Optional[str]
    rule: str


class Rule(BaseModel):
    name: Union[str, RegexKey]
    rule: str
    value: RegexField
    # unit: Optional[Union[str, RegexField]]
    unit: str = ""
    group: Optional[str]
    x: Optional[XField]
    aggr: str = "id"

    def apply(self, lines):
        entries = filter(None, map(self.apply_to_message, lines))
        return group_entries(entries)

    def apply_to_message(self, message):
        if isinstance(self.name, RegexKey):
            name = self.name.apply(message)
        else:
            name = self.name

        value = self.value.apply(message)

        if name is None or value is None:
            return None

        if self.x:
            x = X(name=self.x.name, value=self.x.apply(message))
        else:
            x = None

        return Entry(name=name, value=value, x=x, group=self.group, rule=self.rule)


class AggregationResult(BaseModel):
    name: str
    value: Any
    aggregated_by: str
    unit: str = ""


def merge(a, b, path=None):
    "merges b into a"
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                raise Exception("Conflict at %s" % ".".join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


class RuleBook:
    def __init__(self, rules):
        self.rules = rules

    def apply(self, lines):
        result = {}
        for rule_name, rule in self.rules.items():
            merge(result, rule.apply(lines))

        return result

    def get_aggregated(self, report):
        def aggregate_group(metrics):
            return {
                name: self.aggregate(name, entries) for name, entries in metrics.items()
            }

        return valmap(aggregate_group, report)

    def aggregate(self, name, values):
        rule = self.rules[first(values).rule]

        aggr_fn = aggr_fns[rule.aggr]
        return AggregationResult(
            value=aggr_fn([entry.value for entry in values]),
            name=name,
            aggregated_by=rule.aggr,
            unit=rule.unit,
        )

    def chart(self, values):
        head = first(values)
        if head.x is None:
            return None

        rule = self.rules[head.rule]

        def get_x_value(val, idx):
            return val.x.value

        def get_x_index(val, idx):
            return idx + rule.x.start

        if rule.x.enumerate:
            get_x = get_x_index
        else:
            get_x = get_x_value

        return {
            "label": head.name,
            "data": [
                {"x": get_x(val, idx), "y": val.value} for idx, val in enumerate(values)
            ],
        }

    def get_charts(self, report):
        for groupname, metrics in report.items():
            for name, entries in metrics.items():
                chart = self.chart(entries)
                if chart is not None:
                    yield chart


def group_entries(entries: List[Entry]):
    # grouped just by group
    groups = groupby(attrgetter("group"), entries)

    # create subgroups for each name
    return valmap(groupby(attrgetter("name")), groups)


def parse_config(config):
    return {
        key: Rule.parse_obj({"name": key, "rule": key, **cfg})
        for key, cfg in config.items()
    }
