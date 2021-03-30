from rxport import RuleBook, Rule, get_plot_data

lines = """[2021-03-17 09:55:01] [INFO] gluonts.trainer Epoch[2] Learning rate is 0.001
[2021-03-17 09:55:09] [INFO] gluonts.trainer Epoch[2] Elapsed time 7.835 seconds
[2021-03-17 09:55:09] [INFO] gluonts.trainer Epoch[2] Evaluation metric 'epoch_loss'=5.566774
[2021-03-17 09:55:09] [INFO] gluonts.trainer Epoch[3] Learning rate is 0.001
[2021-03-17 09:55:17] [INFO] gluonts.trainer Epoch[3] Elapsed time 7.553 seconds
[2021-03-17 09:55:17] [INFO] gluonts.trainer Epoch[3] Evaluation metric 'epoch_loss'=5.416297
[2021-03-17 09:55:17] [INFO] gluonts.trainer Epoch[4] Learning rate is 0.001""".splitlines()


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
                "x": "enumerate",
                "x_name": "epoch",
                "x_options": {"data": {"foo": 42}},
            },
        ),
    ]
)


def test_rulebook():
    report = rulebook.apply_all(lines)

    # assert report[0]["learning_rate"]

    assert report.aggregated() == {
        "learning_rate": 0.001,
        "epoch_loss": 5.416297,
    }

    plots = list(get_plot_data(report))
    assert plots == [
        {
            "name": "learning_rate",
            "x": [2, 3, 4],
            "y": [0.001, 0.001, 0.001],
            "options": None,
        },
        {
            "name": "epoch_loss",
            "x": [0, 1],
            "y": [5.566774, 5.416297],
            "options": {"foo": 42},
        },
    ]
