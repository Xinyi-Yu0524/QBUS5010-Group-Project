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
    
    html.H1("Workforce Planning Dashboard"),

# Dashboard - Element A (Filteres)
    html.Div([

        # Function filter
        html.Div([
            html.Label("Functional Area"),
            dcc.Dropdown(id = "function-filter",
            options = [{"label": x, "value": x} for x in sorted (df_wfp["Function"].dropna().unique())], 
            value = sorted(df_wfp["Function"].dropna().unique()), clearable = False, multi = True)
        ]),


        # Location filter
        html.Div([
            html.Label("Location"),
            dcc.Dropdown(id = "location-filter",
                         options = [{"label": x, "value": x} for x in sorted(df_wfp["LOCATION"].dropna().unique())], 
                         value = sorted(df_wfp["LOCATION"].dropna().unique()), clearable = False, multi = True)
        ]),

        # Cost Centre filter
        html.Div([
                    html.Label("Cost Centre"),
                    dcc.Dropdown(id = "cost-centre-filter",
                                 options =  [{"label": x, "value": x} for x in sorted(df_wfp["Cost Centre ID"].dropna().unique())], 
                                 value = sorted(df_wfp["Cost Centre ID"].dropna().unique()), clearable = False, multi = True)
                ]),

        # Talent Acquisition Partner filter
         html.Div([
                    html.Label("Talent Acquisiiton Partner"),
                    dcc.Dropdown(id = "ta-partner-filter",
                                 options = [{"label": x, "value": x} for x in sorted(df_open["Talent Acquisition Partner"].dropna().unique())], 
                                 value = sorted(df_open["Talent Acquisition Partner"].dropna().unique()), clearable = False, multi = True)
                ])
        ], style = {"display": "flex", "gap": "20x"}
        ),


# Dashbboard - Element B (KPIs)
    html.Div([

        # Number of Planned Roles
        html.Div([
            html.P("TOTAL PLANNED ROLES"),
            html.H2(id = "total-roles")
        ]),

        # Number of Filled Roles
        html.Div([
            html.P("FILLED ROLES"),
            html.H2(id = "filled-roles")
        ]),

        # Number of Vacant Roles
        html.Div([
            html.P("VACANT ROLES"),
            html.H2(id = "vacant-roles")
        ]),

        # Vacancy Rate
        html.Div([
            html.P("VACANCY RATE"),
            html.H2(id = "vacant-rate")
        ]),

        # Approved to Hire
        html.Div([
            html.P("APPROVED TO HIRE"),
            html.H2(id = "approved-to-hire")
        ])

    ], style={
        "display": "flex",
        "justifyContent": "space-between"
    })

])


# Callback
@app.callback(
    Output("total-roles", "children"),
    Output("filled-roles", "children"),
    Output("vacant-roles", "children"),
    Output("vacant-rate", "children"),
    Output("approved-to-hire", "children"),

    Input("function-filter", "value"),
    Input("location-filter", "value"),
    Input("cost-centre-filter", "value"),   
    )


# Calculate KPIs
def update_kpis(function, location, cost_centre):
    filtered_df = df_wfp.copy()

    filtered_df = filtered_df[filtered_df["Function"].isin(function)]

    filtered_df = filtered_df[filtered_df["LOCATION"].isin(location)]

    filtered_df = filtered_df[filtered_df["Cost Centre ID"].isin(cost_centre)]

    total = len(filtered_df)
    filled = (filtered_df["ROLE STATUS"] == "Filled").sum()
    vacant = (filtered_df["ROLE STATUS"] == "Vacant").sum()
    vacant_rate = vacant / total if total > 0 else 0

    approved_to_hire = filtered_df["SUB STATUS"].isin(["Actively hiring", "Approved"]).sum()

    return (
        f"{total:,}",
        f"{filled:,}",
        f"{vacant:,}",
        f"{vacant_rate:.1%}",
        f"{approved_to_hire:,}"
    )

# End
app.run(debug=True)



