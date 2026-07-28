"""Minimal Streamlit demo for vizly."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import vizly as vz
from vizly.integrations.streamlit import st_dashboard, st_vizly

st.set_page_config(page_title="vizly Streamlit", layout="wide")
st.title("vizly + Streamlit")

vz.set_theme("corporate")
df = pd.DataFrame(
    {
        "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]),
        "revenue": [12, 18, 15, 22],
        "cost": [5, 7, 6, 9],
    }
)
chart = vz.line(df, x="date", y=["revenue", "cost"], title="Revenue vs cost")
st.subheader("Single chart")
st_vizly(chart, height=420)

bar = vz.bar(df, x="date", y="revenue", title="Revenue")
line = vz.line(df, x="date", y="cost", title="Cost")
st.subheader("Dashboard (ECharts loaded once)")
st_dashboard([bar, line], height=900, title="Ops")
