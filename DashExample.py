#create Dash dashboard to show various electric load profiles

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime as dt
import pandas as pd
import pyodbc

grps = ['Agr','Light','Losses','LrgCI','MedCI',
        'Res','SchA6','SchAD','SmlCom','System']

colors = ['#7DFB6D', '#C7B815', '#D4752E', 
          '#C7583F', '#b2dfdb','#c6ff00']

sources = ['Calibrated', 'Estimated', 'Integrated', 
           'Metered', 'Losses', 'System']

#initialize
app = dash.Dash()
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

#define layout
app.layout = html.Div(children=[
    html.H1(children='DLPs', style={
        'textAlign': 'center',
    }),
    dcc.DatePickerSingle(
        id='date-picker',
        display_format = 'MM/DD/YYYY',
        clearable=True,
        with_portal=True,
        placeholder='Date',
        style = {
                'marginLeft':30,
                'width':'300'
                }
    ),
    dcc.Dropdown(
        id='rategroups',
        options=[{'label': i, 'value': i} for i in grps],
        multi=False,
        placeholder='DLP Rategroup',
        style = {
                'marginLeft':15,
                'marginTop':10,
                'width':'200'
                }
    ),
    dcc.Graph(
        id='DLP Results',
    ),
    html.Div(
        id='hidden_data', 
        style=  {
                'display':'none'
                }
    ),
])
    
@app.callback(
    dash.dependencies.Output('hidden_data','children'),
    [
     dash.dependencies.Input('date-picker','date')
    ]
)

def update_data(date):
    if date == None or date == '':
        return None
    else:
        qry =   """
                    SELECT
                        ltrim(rtrim(rategroup)) rategroup,
                        ltrim(rtrim(source)) source,
                        readhour hour,
                        kwh
                    FROM
                        mk8tfpr_fnl_prof
                    WHERE
                        readdate = '%s'
                    ORDER BY
                        rategroup,
                        source,
                        hour
                """ % date
        cs = 'DSN=mk8d;trusted_connection=true;'
        cnxn = pyodbc.connect(cs)        
        df = pd.read_sql_query(qry, cnxn)
        return df.to_json()

@app.callback(
    dash.dependencies.Output('DLP Results', 'figure'),
    [
     dash.dependencies.Input('hidden_data', 'children'),   
     dash.dependencies.Input('rategroups', 'value')   
    ]
)

def update_scatterplot(data, rategroup):
    if data == None or rategroup == None:
        return None
    else:
        df = pd.read_json(data).sort_values(by=['rategroup','source','hour'])
        sub_df = df[(df['rategroup']==rategroup)]
    
        return {
            'data': [
                go.Scatter(
                    x=sub_df[(sub_df.source == s)]['hour'],
                    y=sub_df[(sub_df.source == s)]['kwh'],
                    text=sub_df[(sub_df.source == s)]['source'],
                    mode='lines+markers',
                    opacity=0.7,
                    marker={
                        'size': 8,
                        'color': color,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name=s
                ) for (s, color) in zip(sources, colors)
            ],
            'layout': go.Layout(
                title=rategroup,
                xaxis=dict(
                    title = 'Hour',
                    dtick=4,
                    showline=True,
                    linewidth=2,
                    automargin=True,
                    zeroline=False
                ),
                yaxis=dict(
                    title = 'kWh',
                    showline=True,
                    linewidth=2,
                    automargin=True,
                    zeroline=False,
                    tickformat=',d'
                ),
                margin={'l': 80, 'b': 20, 't': 20, 'r': 20},
                legend=dict(
                    x = 0.8, 
                    y = 1.1,
                    orientation='h'
                ),
                hovermode='closest'
            )
        }

if __name__ == '__main__':
    app.run_server(debug=True)
