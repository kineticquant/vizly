from __future__ import annotations

import pandas as pd
from django.shortcuts import render

import vizly as vz


def index(request):
    vz.set_theme("corporate")
    df = pd.DataFrame({"region": ["East", "West", "South"], "sales": [40, 32, 28]})
    chart = vz.bar(df, x="region", y="sales", title="Sales")
    return render(request, "index.html", {"chart": chart, "charts": [chart]})
