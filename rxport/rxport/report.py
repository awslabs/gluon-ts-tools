from itertools import chain
from operator import attrgetter
from typing import NamedTuple, Dict, List

from toolz import groupby, first, valmap

from .rule import Rule, Entry


class Report:
    def __init__(self, rules, groups):
        self.rules = rules
        self.groups = groups

    def aggregate_entries(self, entries):
        head = first(entries)
        rule = self.rules[head.rule]
        return rule.aggr(map(attrgetter("value"), entries))

    def aggregated(self):
        return valmap(self.aggregate_entries, self.groups)


class RuleBook:
    def __init__(self, rules):
        self.rules = {rule.rule: rule for rule in rules}

    def _apply_rules(self, message):
        return filter(
            lambda val: val is not None,
            (rule.apply(message) for rule in self.rules.values()),
        )

    def apply_all(self, stream) -> Report:
        # apply each rules to lines

        nested_entries = map(self._apply_rules, stream)
        entries = chain.from_iterable(nested_entries)

        return Report(self.rules, groupby(attrgetter("name"), entries))
