import pandas as pd
import streamlit as st
from boto3.session import Session
from gtstlib import Arn, Resource
from rxport import RuleBook, Rule, get_plot_data

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
                "x": {"rx": r"Epoch\[(\d+)\]", "type": "int", "name": "epoch"},
                "x_name": "epoch",
                "x_options": {"data": {"foo": 42}},
            },
        ),
    ]
)

arn_str = st.text_input("Training-Job ARN")

if not arn_str:
    st.stop()

arn = Arn.parse(arn_str)

session = Session()
profile = st.selectbox("Choose profile: ", session.available_profiles)

if not profile:
    st.stop()

resource = Resource.from_profile(arn, profile)


for log in arn.resource:
    log_events = log.cat()
    lines = [log_evt.message for log_evt in log_events]

    report = rulebook.apply_all(lines)
    plots = list(get_plot_data(report))
    st.title(log.stream_name)
    for plot in plots:
        df = pd.DataFrame(data=plot["y"], index=plot["x"])
        st.subheader(plot["name"])
        st.line_chart(df)
