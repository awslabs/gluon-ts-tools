lines = """[2021-03-17 09:55:01] [INFO] gluonts.trainer Epoch[2] Learning rate is 0.001
[2021-03-17 09:55:09] [INFO] gluonts.trainer Epoch[2] Elapsed time 7.835 seconds
[2021-03-17 09:55:09] [INFO] gluonts.trainer Epoch[2] Evaluation metric 'epoch_loss'=5.566774
[2021-03-17 09:55:09] [INFO] gluonts.trainer Epoch[3] Learning rate is 0.001
[2021-03-17 09:55:17] [INFO] gluonts.trainer Epoch[3] Elapsed time 7.553 seconds
[2021-03-17 09:55:17] [INFO] gluonts.trainer Epoch[3] Evaluation metric 'epoch_loss'=5.416297
[2021-03-17 09:55:17] [INFO] gluonts.trainer Epoch[4] Learning rate is 0.001""".splitlines()


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


rulebook = RuleBook(
    [
        Rule(
            rule="learning_rate",
            name="learning_rate",
            aggr="final",
            value={"rx": "Learning rate is (.*)", "type": "float"},
            meta={
                "x": {"rx": r"Epoch\[(\d+)\]", "type": "int", "name": "epoch"},
                "x_name": "epoch",
            },
        ),
        Rule(
            rule="epoch_loss",
            name="epoch_loss",
            aggr="min",
            value={"rx": r"'epoch_loss'=(.+)", "type": "float"},
            meta={
                # "x": {"rx": r"Epoch\[(\d+)\]", "type": "int", "name": "epoch"},
                "x": "enumerate",
                "x_name": "epoch",
            },
        ),
    ]
)

from toolz import valfilter


def get_plot_data(report):
    rules_with_x = set(
        rule.name for rule in report.rules.values() if rule.meta.get("x") is not None
    )

    for groupname, group in report.groups.items():
        rule_name = first(group).rule
        if rule_name in rules_with_x:
            y = [entry.value for entry in group]

            meta = report.rules[rule_name].meta
            if meta["x"] == "enumerate":
                start = meta.get("x_start", 0)
                x = list(range(start, start + len(y)))
            else:
                x = [entry.meta["x"] for entry in group]

            # yield {
            # "name": groupname,
            # "data": [{"x": xx, "y": yy} for xx, yy in zip(x, y)],
            # }
            yield {"name": groupname, "x": x, "y": y, "options": meta.get("x_options")}


report = rulebook.apply_all(lines)

# print(report.aggregated())

plots = list(get_plot_data(report))
print(plots)
