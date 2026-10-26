# Import the libraries
import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output

# D Element start

# Set the role status and colours
APPROVED_STATUSES = ('Approved', 'Actively hiring')
NO_TA_VALUE = '__NO_TA_RECORDED__'
NO_TA_LABEL = 'No TA recorded'
CATEGORIES = ('With Open Requisition', 'Recruitment Not Started')
NAVY = '#0B1F5E'


# Remove extra spaces from IDs and text
def _text(series):
    text = series.astype('string').str.strip()
    return text.replace('', pd.NA)


# Prepare the data for D
def prepare_d_data(df_wfp, df_open):
    wfp_columns = [
        'ROLE CODE', 'ROLE STATUS', 'SUB STATUS', 'REQUISITION ID',
        'Function', 'LOCATION', 'Cost Centre ID'
    ]
    open_columns = ['Req ID', 'Requisition Status', 'Talent Acquisition Partner']

    # Check the required columns
    for name, df, columns in [
        ('WFP', df_wfp, wfp_columns),
        ('Open Requisition', df_open, open_columns)
    ]:
        missing = sorted(set(columns)-set(df.columns))
        if missing:
            raise ValueError(f'{name}: missing columns {missing}')

    df_roles = df_wfp[wfp_columns].copy()
    df_roles['ROLE CODE'] = _text(df_roles['ROLE CODE'])

    # Each role needs a unique ID
    if df_roles['ROLE CODE'].isna().any() or df_roles['ROLE CODE'].duplicated().any():
        raise ValueError('WFP ROLE CODE must be non-empty and unique')

    df_roles['ROLE STATUS'] = _text(df_roles['ROLE STATUS'])
    df_roles['SUB STATUS'] = _text(df_roles['SUB STATUS'])
    df_roles['_req_key'] = _text(df_roles['REQUISITION ID'])

    df_requests = df_open[open_columns].copy()
    df_requests['_req_key'] = _text(df_requests['Req ID'])

    # Keep open requests with a valid ID found in WFP
    query1 = _text(df_requests['Requisition Status']).eq('Open').fillna(False)
    query2 = df_requests['_req_key'].notna()
    query3 = df_requests['_req_key'].isin(df_roles['_req_key'].dropna())
    df_requests = df_requests[query1 & query2 & query3].copy()

    if df_requests['_req_key'].duplicated().any():
        raise ValueError('Matched Open Req ID must be unique. Check duplicate IDs.')

    # Use the dropdown value when the TA is missing
    df_requests['TA Filter Value'] = _text(df_requests['Talent Acquisition Partner'])
    df_requests['TA Filter Value'] = df_requests['TA Filter Value'].fillna(NO_TA_VALUE)

    # Join Open to WFP and keep roles without a request
    df_roles = df_roles.merge(
        df_requests[['_req_key', 'TA Filter Value']],
        on='_req_key',
        how='left',
        validate='many_to_one',
        indicator=True
    )

    # Check if each role has an open request
    df_roles['Has Open Requisition'] = df_roles['_merge']=='both'
    df_roles['TA Filter Value'] = df_roles['TA Filter Value'].fillna(NO_TA_VALUE)
    df_roles['Talent Acquisition Partner'] = df_roles['TA Filter Value'].replace(
        NO_TA_VALUE, NO_TA_LABEL
    )
    df_roles['Recruitment Status'] = df_roles['Has Open Requisition'].map({
        True: CATEGORIES[0],
        False: CATEGORIES[1]
    })

    # Use the same approved status as B and keep vacant roles
    query1 = df_roles['ROLE STATUS']=='Vacant'
    query2 = df_roles['SUB STATUS'].isin(APPROVED_STATUSES)
    df_d = df_roles[query1 & query2].copy()
    df_d = df_d.drop(columns=['_req_key', '_merge'])
    return df_d


# Filter the roles using the four dropdowns
def filter_d_data(df_d, functions, locations, cost_centres, ta_partners):
    filtered_df = df_d.copy()

    for column, selected in [
        ('Function', functions),
        ('LOCATION', locations),
        ('Cost Centre ID', cost_centres),
        ('TA Filter Value', ta_partners)
    ]:
        if isinstance(selected, str):
            raise ValueError(f'{column} selection must be a list')

        # Show No Data if any filter has no selection
        if selected is None or len(selected)==0:
            return filtered_df.iloc[0:0].copy()

        filtered_df = filtered_df[filtered_df[column].isin(selected)].copy()

    return filtered_df


# Count the roles and calculate recruitment coverage
def summarise_d(filtered_df):
    total = int(filtered_df['ROLE CODE'].nunique())

    query = filtered_df['Has Open Requisition']
    started = int(filtered_df.loc[query, 'ROLE CODE'].nunique())
    not_started = total-started
    coverage_rate = started/total if total else None

    summary = {
        'total': total,
        'started': started,
        'not_started': not_started,
        'coverage_rate': coverage_rate
    }
    return summary


# Draw the donut chart
def build_d_figure(summary):
    total = summary['total']

    if total==0:
        fig = px.pie()
        fig.update_traces(visible=False, showlegend=False)
        fig.add_annotation(
            text='No Data',
            x=0.5, y=0.5,
            xref='paper', yref='paper',
            showarrow=False,
            font={'size': 22, 'color': '#666666'}
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)

    else:
        recruitment_summary = pd.DataFrame({
            'Recruitment Status': list(CATEGORIES),
            'Count': [summary['started'], summary['not_started']]
        })

        fig = px.pie(
            data_frame=recruitment_summary,
            names='Recruitment Status',
            values='Count',
            color='Recruitment Status',
            color_discrete_map={
                CATEGORIES[0]: NAVY,
                CATEGORIES[1]: '#E69F00'
            },
            hole=0.62
        )
        fig.update_traces(
            sort=False,
            direction='clockwise',
            marker={'line': {'color': 'white', 'width': 2}},
            texttemplate='%{value:,} roles<br>%{percent:.1%}',
            textposition='outside',
            hovertemplate='%{label}<br>%{value:,} roles (%{percent:.1%})<extra></extra>'
        )
        fig.add_annotation(
            text=f'<b>{total:,}</b><br>Approved<br>vacancies',
            x=0.5, y=0.5,
            showarrow=False,
            font={'size': 17, 'color': NAVY}
        )

    fig.update_layout(
        template='plotly_white',
        height=380,
        margin={'l': 45, 'r': 45, 't': 30, 'b': 75},
        legend={'orientation': 'h', 'x': 0.5, 'xanchor': 'center', 'y': -0.12},
        paper_bgcolor='white',
        font={'family': 'Arial, sans-serif'}
    )
    return fig


# Show both counts and percentages below the chart
def format_d_summary(summary):
    total = summary['total']

    if not total:
        return 'No approved vacant roles match the selected filters.'

    started = summary['started']
    not_started = summary['not_started']
    return (
        f'With Open Requisition: {started:,} ({started/total:.1%}). '
        f'Recruitment Not Started: {not_started:,} ({not_started/total:.1%}).'
    )


# Set up the D section in the dashboard
def make_d_layout():
    layout = html.Div([
        html.H3('Recruitment Coverage', style={'color': NAVY}),
        html.P(
            'Approved vacant roles with and without an open requisition.',
            style={'fontSize': '13px', 'color': '#595959'}
        ),
        dcc.Graph(
            id='recruitment-coverage-chart',
            config={'displayModeBar': False}
        ),
        html.Div(
            id='recruitment-coverage-summary',
            style={'fontSize': '13px', 'color': '#595959'}
        ),
        html.P(
            ''
            ''
            '',
            style={'fontSize': '12px', 'color': '#6c757d', 'marginTop': '8px'}
        )
    ], style={
        'margin': '20px 10px', 'padding': '18px',
        'border': '1px solid #E6E9EF', 'borderRadius': '10px',
        'backgroundColor': 'white'
    })
    return layout


# Connect the four filters to the chart
def register_d_callback(app, df_d):
    @app.callback(
        Output('recruitment-coverage-chart', 'figure'),
        Output('recruitment-coverage-summary', 'children'),
        Input('function-filter', 'value'),
        Input('location-filter', 'value'),
        Input('cost-centre-filter', 'value'),
        Input('ta-partner-filter', 'value')
    )
    def update_d(functions, locations, cost_centres, ta_partners):
        filtered_df = filter_d_data(
            df_d, functions, locations, cost_centres, ta_partners
        )
        summary = summarise_d(filtered_df)
        fig = build_d_figure(summary)
        message = format_d_summary(summary)
        return fig, message

    return update_d


# D Element end

# E Element start

# Set the TA labels and colour
NO_TA_VALUE = '__NO_TA_RECORDED__'
NO_TA_LABEL = 'No TA recorded'
NAVY = '#0B1F5E'


# Remove extra spaces from IDs and text
def _text(series):
    text = series.astype('string').str.strip()
    return text.replace('', pd.NA)


# Set the order of the recruitment stages
E_STAGES = ('Open/Sourcing', 'Screening', 'Interview', 'Offer')


# Prepare the data for E
def prepare_e_data(df_wfp, df_open):
    wfp_columns = [
        'ROLE CODE', 'REQUISITION ID', 'Function', 'LOCATION', 'Cost Centre ID'
    ]
    open_columns = [
        'Req ID', 'Requisition Status',
        'Requisition Sub status', 'Talent Acquisition Partner'
    ]

    # Check the required columns
    for name, df, columns in [
        ('WFP', df_wfp, wfp_columns),
        ('Open Requisition', df_open, open_columns)
    ]:
        missing = sorted(set(columns)-set(df.columns))
        if missing:
            raise ValueError(f'{name}: missing columns {missing}')

    df_roles = df_wfp[wfp_columns].copy()
    df_roles['_req_key'] = _text(df_roles['REQUISITION ID'])

    # Remove blank request IDs before joining the tables
    df_roles = df_roles[df_roles['_req_key'].notna()].copy()

    df_requests = df_open[open_columns].copy()
    df_requests['Req ID'] = _text(df_requests['Req ID'])

    # Keep all open requests that can be found in WFP
    query1 = _text(df_requests['Requisition Status']).eq('Open').fillna(False)
    query2 = df_requests['Req ID'].notna()
    query3 = df_requests['Req ID'].isin(df_roles['_req_key'])
    df_requests = df_requests[query1 & query2 & query3].copy()

    if df_requests['Req ID'].duplicated().any():
        raise ValueError('Matched Open Req ID must be unique. Check duplicate IDs.')

    # Each matched request needs one WFP record
    query = df_roles['_req_key'].isin(df_requests['Req ID'])
    df_roles = df_roles[query].copy()

    if df_roles['_req_key'].duplicated().any():
        raise ValueError('Each matched request needs one WFP record.')

    # Use WFP for function, location and cost centre
    # Keep matched open requests even if the role is filled
    df_e = df_requests.merge(
        df_roles,
        left_on='Req ID',
        right_on='_req_key',
        how='inner',
        validate='one_to_one'
    )

    # Use Open for the stage and TA
    df_e['Recruitment Stage'] = _text(df_e['Requisition Sub status'])
    df_e['Recruitment Stage'] = df_e['Recruitment Stage'].fillna('No stage recorded')
    df_e['Recruitment Stage'] = df_e['Recruitment Stage'].replace({
        'Open': 'Open/Sourcing',
        'Sourcing': 'Open/Sourcing'
    })

    df_e['TA Filter Value'] = _text(df_e['Talent Acquisition Partner'])
    df_e['TA Filter Value'] = df_e['TA Filter Value'].fillna(NO_TA_VALUE)
    df_e['Talent Acquisition Partner'] = df_e['TA Filter Value'].replace(
        NO_TA_VALUE, NO_TA_LABEL
    )

    df_e = df_e.drop(columns=['_req_key'])
    return df_e


# Filter the requests using the four dropdowns
def filter_e_data(df_e, functions, locations, cost_centres, ta_partners):
    filtered_df = df_e.copy()

    for column, selected in [
        ('Function', functions),
        ('LOCATION', locations),
        ('Cost Centre ID', cost_centres),
        ('TA Filter Value', ta_partners)
    ]:
        if isinstance(selected, str):
            raise ValueError(f'{column} selection must be a list')

        # Show No Data if any filter has no selection
        if selected is None or len(selected)==0:
            return filtered_df.iloc[0:0].copy()

        filtered_df = filtered_df[filtered_df[column].isin(selected)].copy()

    return filtered_df


# Count the open requests at each stage
def summarise_e(filtered_df):
    counts = filtered_df.groupby('Recruitment Stage')['Req ID'].nunique()
    stage_order = list(E_STAGES)

    # Keep any extra stage names in the result
    for stage in counts.index:
        if stage not in stage_order:
            stage_order.append(stage)

    stage_summary = counts.reindex(stage_order, fill_value=0).reset_index()
    stage_summary.columns = ['Recruitment Stage', 'Count']
    return stage_summary


# Draw the horizontal bar chart
def build_e_figure(stage_summary):
    total = int(stage_summary['Count'].sum())

    if total==0:
        fig = px.bar()
        fig.update_traces(visible=False, showlegend=False)
        fig.add_annotation(
            text='No Data',
            x=0.5, y=0.5,
            xref='paper', yref='paper',
            showarrow=False,
            font={'size': 22, 'color': '#666666'}
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)

    else:
        fig = px.bar(
            data_frame=stage_summary,
            x='Count',
            y='Recruitment Stage',
            orientation='h',
            text='Count',
            color_discrete_sequence=[NAVY]
        )
        fig.update_traces(textposition='outside', cliponaxis=False)
        fig.update_xaxes(
            title_text='Number of open requisitions',
            range=[0, stage_summary['Count'].max()*1.15]
        )
        fig.update_yaxes(
            title_text='Recruitment stage',
            categoryorder='array',
            categoryarray=stage_summary['Recruitment Stage'].tolist(),
            autorange='reversed'
        )

        # Use whole numbers when only a few requests are selected
        if stage_summary['Count'].max()<=5:
            fig.update_xaxes(dtick=1)

    fig.update_layout(
        template='plotly_white',
        height=380,
        margin={'l': 30, 'r': 45, 't': 30, 'b': 55},
        paper_bgcolor='white',
        font={'family': 'Arial, sans-serif'},
        showlegend=False
    )
    return fig


# Show the total number of open requests
def format_e_summary(stage_summary):
    total = int(stage_summary['Count'].sum())

    if total==0:
        return 'No open requisitions match the selected filters.'

    return f'Open requisitions: {total:,}.'


# Set up the E section in the dashboard
def make_e_layout():
    layout = html.Div([
        html.H3('Open Requisitions by Recruitment Stage', style={'color': NAVY}),
        html.P(
            '',
            style={'fontSize': '13px', 'color': '#595959'}
        ),
        dcc.Graph(
            id='recruitment-stage-chart',
            config={'displayModeBar': False}
        ),
        html.Div(
            id='recruitment-stage-summary',
            style={'fontSize': '13px', 'color': '#595959'}
        )
    ], style={
        'margin': '20px 10px', 'padding': '18px',
        'border': '1px solid #E6E9EF', 'borderRadius': '10px',
        'backgroundColor': 'white'
    })
    return layout


# Connect the four filters to the E chart
def register_e_callback(app, df_e):
    @app.callback(
        Output('recruitment-stage-chart', 'figure'),
        Output('recruitment-stage-summary', 'children'),
        Input('function-filter', 'value'),
        Input('location-filter', 'value'),
        Input('cost-centre-filter', 'value'),
        Input('ta-partner-filter', 'value')
    )
    def update_e(functions, locations, cost_centres, ta_partners):
        filtered_df = filter_e_data(
            df_e, functions, locations, cost_centres, ta_partners
        )
        stage_summary = summarise_e(filtered_df)
        fig = build_e_figure(stage_summary)
        message = format_e_summary(stage_summary)
        return fig, message

    return update_e


# E Element end

# F Element start

# Set the chart colour
NAVY = '#0B1F5E'


# Find the last date in the full data before using filters
def get_f_report_date(df_closed):
    columns = ['Recruiting Start Date', 'Offer Date']
    missing = sorted(set(columns)-set(df_closed.columns))

    if missing:
        raise ValueError(f'Closed Requisition: missing columns {missing}')

    dates = []
    for column in columns:
        dates.append(pd.to_datetime(df_closed[column], errors='coerce'))

    report_date = pd.concat(dates, ignore_index=True).max()

    if pd.isna(report_date):
        raise ValueError('No valid date is available for the report date.')

    return report_date.normalize()


# Prepare the data for F
def prepare_f_data(df_closed):
    columns = ['Req ID', 'Function', 'Location', 'Recruiting Start Date', 'Offer Date',
        'Cost Centre ID', 'Talent Acquisition Partner'
    ]
    missing = sorted(set(columns)-set(df_closed.columns))

    if missing:
        raise ValueError(f'Closed Requisition: missing columns {missing}')

    df_f = df_closed[columns].copy()

    # Add the TA values for the filter
    df_f['TA Filter Value'] = df_f['Talent Acquisition Partner']
    
    # Remove extra spaces from IDs and text
    for column in ['Req ID', 'Function', 'Location']:
        text = df_f[column].astype('string').str.strip()
        df_f[column] = text.replace('', pd.NA)

    if df_f['Req ID'].isna().any() or df_f['Req ID'].duplicated().any():
        raise ValueError('Closed Req ID must be non-empty and unique.')

    # Read both dates and use calendar days
    for column in ['Recruiting Start Date', 'Offer Date']:
        df_f[column] = pd.to_datetime(df_f[column], errors='coerce')
        df_f[column] = df_f[column].dt.normalize()

    # Treat Offer Date as the date the offer was made
    df_f['Days to Offer'] = (
        df_f['Offer Date']-df_f['Recruiting Start Date']
    ).dt.days

    # Keep valid dates, including offers made on the same day
    query1 = df_f['Recruiting Start Date'].notna()
    query2 = df_f['Offer Date'].notna()
    query3 = df_f['Days to Offer']>=0
    df_f = df_f[query1 & query2 & query3].copy()

    # Group each record by the month of its offer
    df_f['Offer Month'] = df_f['Offer Date'].dt.strftime('%Y-%m')
    return df_f


# Filter F using all four filters
def filter_f_data(df_f, functions, locations, cost_centres, ta_partners):
    # Show No Data if a filter has no selection
    if not functions or not locations or not cost_centres or not ta_partners:
        return df_f.iloc[:0].copy()

    query1 = df_f['Function'].isin(functions)
    query2 = df_f['Location'].isin(locations)
    query3 = df_f['Cost Centre ID'].isin(cost_centres)
    query4 = df_f['TA Filter Value'].isin(ta_partners)

    filtered_df = df_f[query1 & query2 & query3 & query4].copy()
    return filtered_df


# Calculate the monthly average and the overall average
def summarise_f(filtered_df, report_date):
    if report_date is None or pd.isna(report_date):
        raise ValueError('A valid report date is required.')

    end_date = pd.Timestamp(report_date).normalize()

    # Use the report month and the previous 11 months
    last_month = end_date.to_period('M')
    months = pd.period_range(end=last_month, periods=12, freq='M')
    start_date = months[0].start_time

    # Use offer dates to select the records in this period
    query1 = filtered_df['Offer Date']>=start_date
    query2 = filtered_df['Offer Date']<=end_date
    records = filtered_df[query1 & query2].copy()

    # Calculate the mean and number of records for each month
    averages = records.groupby('Offer Month')['Days to Offer'].mean().reset_index()
    averages.columns = ['Offer Month', 'Average Days']

    counts = records.groupby('Offer Month')['Req ID'].nunique().reset_index()
    counts.columns = ['Offer Month', 'Records']

    # Keep all 12 months in time order
    monthly = pd.DataFrame({
        'Offer Month': months.strftime('%Y-%m'),
        'Month Label': months.strftime('%b %Y')
    })
    monthly = monthly.merge(averages, on='Offer Month', how='left')
    monthly = monthly.merge(counts, on='Offer Month', how='left')

    # Only fill missing counts with zero, leaving the average blank
    monthly['Records'] = monthly['Records'].fillna(0).astype(int)

    # Use all records for the overall mean, not the monthly means
    average_days = float(records['Days to Offer'].mean())
    total = int(records['Req ID'].nunique())

    return {
        'monthly': monthly,
        'average_days': average_days,
        'total': total,
        'start_date': start_date,
        'end_date': end_date
    }


# Draw the monthly line chart
def build_f_figure(summary):
    monthly = summary['monthly']

    if summary['total']==0:
        fig = px.line()
        fig.update_traces(visible=False, showlegend=False)
        fig.add_annotation(
            text='No Data',
            x=0.5, y=0.5,
            xref='paper', yref='paper',
            showarrow=False,
            font={'size': 22, 'color': '#666666'}
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)

    else:
        fig = px.line(
            data_frame=monthly,
            x='Offer Month',
            y='Average Days',
            markers=True,
            custom_data=['Records'],
            color_discrete_sequence=[NAVY]
        )
        fig.update_traces(
            connectgaps=False,
            line={'width': 3},
            marker={'size': 8},
            hovertemplate=(
                'Offer month: %{x}<br>'
                'Average: %{y:.1f} days<br>'
                'Records: %{customdata[0]:,}<extra></extra>'
            )
        )
        # Keep the month and record count together
        month_ticks = []
        for month, count in zip(monthly['Month Label'], monthly['Records']):
            month_ticks.append(f'{month}<br>n={count}')

        fig.update_xaxes(
            title_text='Offer month (n = monthly records)',
            title_standoff=20,
            tickangle=0,
            type='category',
            categoryorder='array',
            categoryarray=monthly['Offer Month'].tolist(),
            tickmode='array',
            tickvals=monthly['Offer Month'].tolist(),
            ticktext=month_ticks
        )
        fig.update_yaxes(title_text='Average time to offer (days)', rangemode='tozero')

    fig.update_layout(
        template='plotly_white',
        height=420,
        margin={'l': 55, 'r': 35, 't': 30, 'b': 95},
        paper_bgcolor='white',
        font={'family': 'Arial, sans-serif'},
        showlegend=False
    )
    return fig


# Show the average as a simple number
def format_f_average(summary):
    if summary['total']==0:
        return 'No Data'

    return f"{summary['average_days']:.1f} days"


# Show the number of records and the date range
def format_f_summary(summary):
    start = summary['start_date'].strftime('%d %b %Y')
    end = summary['end_date'].strftime('%d %b %Y')

    if summary['total']==0:
        return f'No offer records match the selected filters from {start} to {end}.'

    return f"{summary['total']:,} records - Offers from {start} to {end}."


# Set up the F section in the dashboard
def make_f_layout():
    layout = html.Div([
        html.H3('Average Time to Offer - Past 12 Months', style={'color': NAVY}),
        html.P(
            'Closed recruitment records - Function and Location filters apply. '
            '',
            style={'fontSize': '13px', 'color': '#595959'}
        ),
        html.Div(
            id='time-to-offer-average',
            style={'fontSize': '28px', 'fontWeight': 'bold', 'color': NAVY}
        ),
        html.Div(
            id='time-to-offer-summary',
            style={'fontSize': '13px', 'color': '#595959'}
        ),
        dcc.Graph(
            id='time-to-offer-chart',
            config={'displayModeBar': False}
        ),
        html.P(
            'Days from recruiting start to offer made. '
            'n shows the number of records in each month.',
            style={'fontSize': '12px', 'color': '#595959'}
        )
    ], style={
        'margin': '20px 10px', 'padding': '18px',
        'border': '1px solid #E6E9EF', 'borderRadius': '10px',
        'backgroundColor': 'white'
    })
    return layout


# Connect the four filters to F
def register_f_callback(app, df_f, report_date):
    @app.callback(
        Output('time-to-offer-chart', 'figure'),
        Output('time-to-offer-average', 'children'),
        Output('time-to-offer-summary', 'children'),
        Input('function-filter', 'value'),
        Input('location-filter', 'value'),
        Input('cost-centre-filter', 'value'),
        Input('ta-partner-filter', 'value')
    )
    def update_f(functions, locations, cost_centres, ta_partners):
        filtered_df = filter_f_data(
            df_f, functions, locations, cost_centres, ta_partners
        )
        summary = summarise_f(filtered_df, report_date)
        fig = build_f_figure(summary)
        average = format_f_average(summary)
        message = format_f_summary(summary)
        return fig, average, message

    return update_f


# F Element end
