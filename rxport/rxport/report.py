from .rule import Entry


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
