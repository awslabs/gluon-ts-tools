from toolz import first


def get_plot_data(report):
    rules_with_x = set(
        rule.name
        for rule in report.rules.values()
        if rule.meta.get("x") is not None
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

            options = meta.get("x_options")
            if options:
                options = options.data

            yield {
                "name": groupname,
                "x": x,
                "y": y,
                "options": options,
            }
