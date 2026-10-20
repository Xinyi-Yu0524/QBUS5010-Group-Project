import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

from dash import Dash, dcc, html, Input, Output

import dash_bootstrap_components as dbc

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

# Define colour
Navy = "#0B1F5E"


# Dash
app = Dash(__name__ ,external_stylesheets=[dbc.themes.FLATLY,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"])

app.layout = html.Div([
    
    html.H1("Workforce Planning Dashboard",
            style = {"fontSize": "30px",
                     "fontWeight": "700",
                     "color": Navy,
                     "marginBottom": "2px"}),

    html.P( f"As at {date.today().strftime('%d %B %Y')}",
           style = {"fontSuze": "14px",
                    "color": "#6c757D",
                    "marginBottom": "20x"}
            ),

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
    dbc.Row([

    # Number of planned roles
    dbc.Col([
            dbc.Card([
                dbc.CardBody([

            html.Div(
                html.I(
                    className="bi bi-people-fill",
                    style={
                        "fontSize": "20px"
                    }
                ),
                style={
                    "backgroundColor": Navy,
                    "color": "white",
                    "borderRadius": "50%",
                    "width": "42px",
                    "height": "42px",
                    "minWidth": "42px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontSize": "21px",
                    "marginRight": "12px"
                }
            ),

        html.Div([
            html.P("TOTAL PLANNED ROLES", 
                   style={
                        "fontSize": "12px",
                        "color": "#6C757D",
                        "marginBottom": "2px"
                    }),
            html.H3(id = "total-roles", 
                    style={
                        "fontSize": "26px",
                        "fontWeight": "700",
                        "color": Navy,
                        "marginBottom": "0"
                    })
        ])
        ],  style={
            "display": "flex",
            "alignItems": "center",
            "padding": "18px"}
        )], 
        className="shadow-sm h-100",
        style={
            "border": "1px solid #E6E9EF",
            "borderRadius": "10px"}
        
        )], width  = True),

    # Number of filled roles
    dbc.Col([
        dbc.Card([
                dbc.CardBody([

            html.Div(
                html.I(
                    className="bi bi-person-check-fill",
                    style={"fontSize": "20px"}
                        ),
                style={
                    "backgroundColor": Navy,
                    "color": "white",
                    "borderRadius": "50%",
                    "width": "42px",
                    "height": "42px",
                    "minWidth": "42px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontSize": "21px",
                    "marginRight": "12px"
                }
            ),

        html.Div([
            html.P("FILLED ROLES", 
                   style={
                        "fontSize": "12px",
                        "color": "#6C757D",
                        "marginBottom": "2px"
                    }),
            html.H3(id = "filled-roles", 
                    style={
                        "fontSize": "26px",
                        "fontWeight": "700",
                        "color": Navy,
                        "marginBottom": "0"
                    })
        ])
        ],  style={
            "display": "flex",
            "alignItems": "center",
            "padding": "18px"}
        )], 
        className="shadow-sm h-100",
        style={
            "border": "1px solid #E6E9EF",
            "borderRadius": "10px"}
        
        )], width = True),

    # Number of vacant roles
    dbc.Col([
                     dbc.Card([
                         dbc.CardBody([
         
                     html.Div(
                         html.I(
                            className="bi bi-person-dash",
                            style={"fontSize": "20px"}),

                         style={
                             "backgroundColor": Navy,
                             "color": "white",
                             "borderRadius": "50%",
                             "width": "42px",
                             "height": "42px",
                             "minWidth": "42px",
                             "display": "flex",
                             "alignItems": "center",
                             "justifyContent": "center",
                             "fontSize": "21px",
                             "marginRight": "12px"
                         }
                     ),
         
                 # Number of Planned Roles
                 html.Div([
                     html.P("VACANT ROLES", 
                            style={
                                 "fontSize": "12px",
                                 "color": "#6C757D",
                                 "marginBottom": "2px"
                             }),
                     html.H3(id = "vacant-roles", 
                             style={
                                 "fontSize": "26px",
                                 "fontWeight": "700",
                                 "color": Navy,
                                 "marginBottom": "0"
                             })
                 ])
                 ],  style={
                     "display": "flex",
                     "alignItems": "center",
                     "padding": "18px"}
                 )], 
                 className="shadow-sm h-100",
                 style={
                     "border": "1px solid #E6E9EF",
                     "borderRadius": "10px"}
                 
                 )], width = True),

    # Number of vacancy rate
    dbc.Col([
            dbc.Card([
                dbc.CardBody([

            html.Div(
                html.I(
                    className="bi bi-percent",
                    style={"fontSize": "20px"}),

                style={
                    "backgroundColor": Navy,
                    "color": "white",
                    "borderRadius": "50%",
                    "width": "42px",
                    "height": "42px",
                    "minWidth": "42px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontSize": "21px",
                    "marginRight": "12px"
                }
            ),

        # Number of Planned Roles
        html.Div([
            html.P("VACANCY RATE", 
                   style={
                        "fontSize": "12px",
                        "color": "#6C757D",
                        "marginBottom": "2px"
                    }),
            html.H3(id = "vacant-rate", 
                    style={
                        "fontSize": "26px",
                        "fontWeight": "700",
                        "color": Navy,
                        "marginBottom": "0"
                    })
        ])
        ],  style={
            "display": "flex",
            "alignItems": "center",
            "padding": "18px"}
        )], 
        className="shadow-sm h-100",
        style={
            "border": "1px solid #E6E9EF",
            "borderRadius": "10px"}
        
        )], width = True),

    # Number of approved to hire
    dbc.Col([
            dbc.Card([
                dbc.CardBody([

            html.Div(
                html.I(
                    className="bi bi-person-plus-fill",
                    style={"fontSize": "20px"}),

                style={
                    "backgroundColor": Navy,
                    "color": "white",
                    "borderRadius": "50%",
                    "width": "42px",
                    "height": "42px",
                    "minWidth": "42px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "fontSize": "21px",
                    "marginRight": "12px"
                }
            ),

        # Number of Planned Roles
        html.Div([
            html.P("APPROVED TO HIRE", 
                   style={
                        "fontSize": "12px",
                        "color": "#6C757D",
                        "marginBottom": "2px"
                    }),
            html.H3(id = "approved-to-hire", 
                    style={
                        "fontSize": "26px",
                        "fontWeight": "700",
                        "color": Navy,
                        "marginBottom": "0"
                    })
        ])
        ],  style={
            "display": "flex",
            "alignItems": "center",
            "padding": "18px"})
            
        ], 
        className="shadow-sm h-100",
        style={
            "border": "1px solid #E6E9EF",
            "borderRadius": "10px"}
        )
        ], width = True)

    ], className = "gx-3", 
        style ={"border": "3px dashed #B8C0CC", "borderRadius": "10px","paddingTop":"6px", "paddingBottom":"6px", "paddingLeft": "6px", "paddingRight": "6px", "margin": "5px 10px 20px 10px"})


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



