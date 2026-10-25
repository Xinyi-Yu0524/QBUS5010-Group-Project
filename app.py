import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

from dash import Dash, dcc, html, Input, Output, dash_table

import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

# Import the D, E and F sections
from element_def import (
    prepare_d_data, make_d_layout, register_d_callback,
    prepare_e_data, make_e_layout, register_e_callback,
    get_f_report_date, prepare_f_data, make_f_layout, register_f_callback
)


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
# Group time to offer based on the month of Offer Date - line chart

df_wfp["FTE_actual"] = df_wfp["FTE"] / 100


# Element C : Function-Level workforce summary
wfp_summary = (
    df_wfp.groupby("Function")
    .agg(
        Total=("ROLE CODE", "nunique"),
        Filled=("ROLE STATUS", lambda x: (x == "Filled").sum()),
        Vacant=("ROLE STATUS", lambda x: (x == "Vacant").sum()),
        Approved=("SUB STATUS", lambda x: (x == "Approved").sum()),
        Actively_Hiring=("SUB STATUS", lambda X: (X == "Actively hiring").sum())     
    )
    .reset_index()
)

wfp_summary["Vacancy Rate"] = (
    wfp_summary["Vacant"] / wfp_summary["Total"]
)

wfp_summary = wfp_summary[
    [
        "Function",
        "Total",
        "Filled",
        "Vacant",
        "Vacancy Rate",
        "Approved",
        "Actively_Hiring"
    ]
]

wfp_summary = wfp_summary.rename(
    columns={"Actively_Hiring": "Actively Hiring"}
)

# Prepare the data for D, E and F
df_d = prepare_d_data(df_wfp, df_open)
df_e = prepare_e_data(df_wfp, df_open)
report_date = get_f_report_date(df_close)
df_f = prepare_f_data(df_close)

# Define colour
Navy = "#0B1F5E"


# Dash
app = Dash(__name__ ,external_stylesheets=[dbc.themes.FLATLY,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"])

app.layout = html.Div(style={"padding": "24px", "fontFamily": "Arial, sans-serif"}, children=[
    
    html.H1("Workforce Planning Dashboard",
            style = {"fontSize": "30px",
                     "fontWeight": "700",
                     "color": Navy,
                     "marginBottom": "2px"}),

    html.P( "Simulated data - workforce and recruitment records for a fictional organisation.",
           style = {"fontSuze": "14px",
                    "color": "#6c757D",
                    "marginBottom": "20x"}
            ),

html.P(
    "Select one or more options. Use search to find an option, Deselect All to clear selections, and Select All to restore all options.",
    style={"fontSize": "13px", "color": "#6c757d", "marginBottom": "12px"}
),

# Dashboard - Element A (Filteres)
    html.Div([

        # Function filter
        html.Div([
            html.Label("Functional Area"),
            dcc.Dropdown(id = "function-filter",
            options = [{"label": x, "value": x} for x in sorted (df_wfp["Function"].dropna().unique())], 
            value = sorted(df_wfp["Function"].dropna().unique()), clearable=True, multi=True, searchable=True)
        ]),


        # Location filter
        html.Div([
            html.Label("Location"),
            dcc.Dropdown(id = "location-filter",
                         options = [{"label": x, "value": x} for x in sorted(df_wfp["LOCATION"].dropna().unique())], 
                         value = sorted(df_wfp["LOCATION"].dropna().unique()), clearable=True, multi=True, searchable=True)
        ]),

        # Cost Centre filter
        html.Div([
                    html.Label("Cost Centre"),
                    dcc.Dropdown(id = "cost-centre-filter",
                                 options =  [{"label": x, "value": x} for x in sorted(df_wfp["Cost Centre ID"].dropna().unique())], 
                                 value = sorted(df_wfp["Cost Centre ID"].dropna().unique()), clearable=True, multi=True, searchable=True)
                ]),

        # Talent Acquisition Partner filter
         html.Div([
                    html.Label("Talent Acquisiton Partner"),
                    dcc.Dropdown(id = "ta-partner-filter",
                                 options = [
                                    {"label": x, "value": x}
                                    for x in sorted(df_open["Talent Acquisition Partner"].dropna().unique())
                                 ] + [{"label": "No TA recorded", "value": "__NO_TA_RECORDED__"}],

                                 value = sorted(df_open["Talent Acquisition Partner"].dropna().unique()) + ["__NO_TA_RECORDED__"], clearable=True, multi=True, searchable=True)


                ])
        ], style={"display": "grid", "gridTemplateColumns": "repeat(4, minmax(0, 1fr))", "gap": "20px"}
        ),

html.Button(
    "Reset filters",
    id="reset-filters",
    n_clicks=0,
    style={
        "backgroundColor": Navy,
        "color": "white",
        "border": "none",
        "borderRadius": "6px",
        "padding": "8px 16px",
        "fontSize": "14px",
        "cursor": "pointer",
        "marginTop": "12px",
        "marginBottom": "12px"
    }
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
        style ={"border": "3px dashed #B8C0CC", "borderRadius": "10px","paddingTop":"6px", "paddingBottom":"6px", "paddingLeft": "6px", "paddingRight": "6px", "margin": "5px 10px 20px 10px"}),
        html.Div([
            html.H3("Workforce by Function"),
            dash_table.DataTable(
                id="function-summary-table",
                columns=[
                    {
                        "name": col, 
                        "id": col,
                        "type":"numeric",
                        "format": {"specifier": ".1%"}
                    }
                    if col == "Vacancy Rate"
                    else {
                        "name": col,
                        "id": col,
                        "type": "text" if col == "Function" else "numeric"
                    }
                    for col in wfp_summary.columns
                ],
                data=wfp_summary.to_dict("records"),
                sort_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"padding": "10px", "textAlign": "right", "fontFamily": "Arial, sans-serif"},
                style_cell_conditional=[
                    {
                        "if": {"column_id": "Function"},
                        "textAlign": "left"
                    }
                ],          
                style_header={
                    "backgroundColor": Navy,
                    "color": "white",
                    "fontWeight": "bold",
                    "fontFamily": "Arial, sans-serif"
                }
            ),
            html.Div(
                id="function-summary-message",
                style={
                    "textAlign": "center",
                    "fontWeight": "bold",
                    "fontSize": "16px",
                    "color": "#666666",
                    "padding": "24px"
                }
            ),
            html.P(
                "Vacancy Rate = Vacant / Total roles. Approved and Actively Hiring are shown as separate sub-status counts.",                    
                style={
                    "fontSize": "13px",
                    "color": "#595959",
                    "marginTop": "8px",
                    "marginBottom": "0"
                }
            ),
        ], style={"margin": "20px 10px"}),

    # Show D, E and F below the workforce table
    make_d_layout(),
    make_e_layout(),
    make_f_layout()

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

@app.callback(
    Output("function-summary-table", "data"),
    Input("function-filter", "value"),
    Input("location-filter", "value"),
    Input("cost-centre-filter", "value")
)
def upadate_function_summary(function,location,cost_centre):
    filtered_df = df_wfp[
        df_wfp["Function"].isin(function)
        & df_wfp["LOCATION"].isin(location)
        & df_wfp["Cost Centre ID"].isin(cost_centre)
    ]

    summary = (
        filtered_df.groupby("Function")
        .agg(
            Total=("ROLE CODE", "nunique"),
            Filled=("ROLE STATUS", lambda x: (x == "Filled").sum()),
            Vacant=("ROLE STATUS", lambda x: (x == "Vacant").sum()),
            Approved=("SUB STATUS", lambda x: (x == "Approved").sum()),
            Actively_Hiring=("SUB STATUS", lambda x: (x == "Actively hiring").sum())
             
        )
        .reset_index()
    )

    summary["Vacancy Rate"] = summary["Vacant"] / summary["Total"]
    summary = summary.rename(
        columns={"Actively_Hiring": "Actively Hiring"}
    )

    return summary[
        [
            "Function",
            "Total",
            "Filled",
            "Vacant",
            "Vacancy Rate",
            "Approved",
            "Actively Hiring"
        ]
    ].to_dict("records")

@app.callback(
    Output("function-summary-message", "children"),
    Input("function-summary-table", "data")
)
def update_summary_message(rows):
    if not rows:
        return "No roles match the selected filters. Please adjust your selection."
    return""

@app.callback(
    Output("function-summary-table", "style_data_conditional"),
    Input("function-summary-table", "data")
)
def update_vacancy_bars(rows):
    styles = []

    for row in rows or []:
        rate = row["Vacancy Rate"]
        width = rate * 100

        styles.append({
            "if": {
                "filter_query": f"{{Vacancy Rate}} = {rate}",
                "column_id": "Vacancy Rate"
            },
            "background": (
                f"linear-gradient(90deg,"
                f"#D6E4F5 0%, #D6E4F5 {width}%,"
                f"transparent {width}%, transparent 100%)"
            )
        })

    return styles

@app.callback(
    Output("function-filter", "value"),
    Output("location-filter", "value"),
    Output("cost-centre-filter", "value"),
    Output("ta-partner-filter", "value"),
    Input("reset-filters", "n_clicks"),
    prevent_initial_call=True
)
def reset_all_filters(n_clicks):
    return(
        sorted(df_wfp["Function"].dropna().unique()),
        sorted(df_wfp["LOCATION"].dropna().unique()),
        sorted(df_wfp["Cost Centre ID"].dropna().unique()),
        sorted(df_open["Talent Acquisition Partner"].dropna().unique()) + ["__NO_TA_RECORDED__"]
    )





# Connect D, E and F to the dashboard filters
register_d_callback(app, df_d)
register_e_callback(app, df_e)
register_f_callback(app, df_f, report_date)

# End
if __name__=='__main__':
    app.run(debug=True, host="0.0.0.0", port=8050)



