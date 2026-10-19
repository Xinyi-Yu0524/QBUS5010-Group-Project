import pandas as pd
import numpy as np
from pathlib import Path

from dash import Dash, dcc, html, Input, Output

import plotly.express as px
import plotly.graph_objects as go

# Import datasets

base = Path("data")

df_employee = pd.read_excel(base / "Employee Roster.xlsx")
df_wfp = pd.read_excel(base / "WFP.xlsx")
df_open = pd.read_excel(base / "Open Requisition.xlsx")
df_close = pd.read_excel(base / "Closed Requisition.xlsx")

'''
# No missing data in the necessary columns

df_open["Requisition Sub status"].value_counts(dropna=False)
df_wfp["Function"].value_counts(dropna=False)
df_wfp["ROLE STATUS"].value_counts(dropna=False)
df_wfp["SUB STATUS"].value_counts(dropna=False)
'''

# Data Manipulation
# In the WFP dataset, FTE needs to change from the figure of the percentage number, e.g., 100 to the actual figure, e.g., 1.
# Get the percentage of open requisitions among all approved vacant roles - donut chart
# In the close requisition dataset, create a column for time-to-offer
# Group time to offer based on the month of Recruitment Start Date - line chart

df_wfp["FTE_actual"] = df_wfp["FTE"] / 100


# Element C Function Level Table - dataframe: wfp_summary

wfp_summary = pd.crosstab(df_wfp["Function"],df_wfp["ROLE STATUS"])
wfp_summary["Total"] = wfp_summary.sum(axis=1)

# Vacant Rate needs to be displayed as a percentage in Dash
wfp_summary["Vacant Rate"] = (wfp_summary["Vacant"] / wfp_summary["Total"])

approved = (df_wfp[df_wfp["SUB STATUS"] == "Approved"].groupby("Function").size())

wfp_summary["Approved to Hire"] = approved.reindex(wfp_summary.index, fill_value=0)

wfp_summary.columns.name = None
wfp_summary = wfp_summary.reset_index()

wfp_summary = wfp_summary[["Total", "Filled", "Vacant", "Vacant Rate", "Approved to Hire"]]


# Element D Pie/Donut Chart - dataframe: recruitment_summary

df_hiring = df_wfp[df_wfp["SUB STATUS"].isin(["Actively hiring", "Approved"])].copy()
df_hiring["Recruitment Status"] = df_hiring["REQUISITION ID"].notna().map({True: "Started",False: "Not Started"})

recruitment_summary = (df_hiring["Recruitment Status"].value_counts().reset_index())
recruitment_summary.columns = ["Recruitment Status", "Count"]


# Element F Line Chart dataframe:

df_close["Time to Offer"] = (df_close["Offer Date"] - df_close["Recruiting Start Date"]).dt.days

df_close["Recruiting_Year_Month"] = (
    df_close["Recruiting Start Date"].dt.to_period("M")
)

time_to_offer_by_month = (df_close.groupby("Recruiting_Year_Month")["Time to Offer"].mean().round(1).reset_index())


# Dash
app = Dash(__name__)

app.layout = html.Div([
    
    html.H1("Workforce Planning Dashboard")
    
])

# Dashboard




# End
app.run(debug=True)



