#!/usr/bin/python
# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd

print('Opening and preparing data...', end='')

df = pd.read_csv('datasets/telecom_dataset.csv')
df = df.dropna()
df = df.drop_duplicates().reset_index(drop=True)

df['internal'] = df['internal'].astype('str') # преобразуется в str иначе возникает известный конфликт типов между numpy и python
df['date'] = pd.to_datetime(df['date'])
df['date_agg'] = pd.to_datetime(df['date'].dt.date)

print('OK')
print('Making layout...', end='')

dash_note = '''
            Интерактивные данные для телеком проекта сервиса "Нупозвони". Яндекс.Практикум
            '''

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(children=[
    html.H2(children = 'Сервис "Нупозвони"', style={'textAlign': 'center'}),
    html.Label(dash_note, style={'textAlign': 'center'}),
    html.Br(),
    html.Div([
        html.Div([
            html.H5(children= 'Набор №1'),
            html.Label('Фильтр по направлению вызовов:'),
            dcc.Dropdown(
                options = [{'label': 'Входящие', 'value': 'in'}, {'label': 'Исходящие', 'value': 'out'}],
                value = df['direction'].unique().tolist(),
                style = {'width':'60%'},
                multi = True,
                id = 'direction_selector'),
            
        ], className = 'six columns'),
        html.Div([
                html.H5(children= 'Набор №2'),
                html.Label('Тип вызова:'),
                dcc.Dropdown(
                options = [{'label': 'Внутренние', 'value': 'True'}, {'label': 'Внешние', 'value': 'False'}],
                value = df['internal'].unique().tolist(),
                style = {'width':'60%'},
                multi = True,
                id = 'is_internal_selector'),
            ], className = 'six columns'),
        ], className='row'),

    html.Div([
        html.Div([
            html.Label('Гистограмма распределения длительности звонков'),
            dcc.Graph(
                id = 'call-durations',
                style = {'height':'25vw'}
            ),
            html.Br(),
            html.Label('Диаграмма соотношения внутренних и внешних вызовов'),
            dcc.Graph(
                id = 'pie-is-internal-calls',
                style = {'height':'25vw'},
            ),
        ], className = 'six columns'),

        html.Div([
            html.Label('Диаграмма количества вызовов по дням'),
            dcc.Graph(
                id = 'calls-per-day',
                style = {'height':'25vw'}
            ),
            html.Br(),
            html.Label('Диаграмма соотношения входящих и исходящих вызовов'),
            dcc.Graph(
                id = 'pie-in-out-calls',
                style = {'height':'25vw'},
            ),
        ], className = 'six columns'),
    ], className='row'),         
    ])
print('OK')

print('Working on logic and graphics...')

@app.callback(
    [Output('call-durations', 'figure'), 
    Output('pie-is-internal-calls', 'figure'), 
    Output('calls-per-day', 'figure'),
    Output('pie-in-out-calls', 'figure')
    ],   
    [Input('direction_selector','value'), 
    Input('is_internal_selector','value'),]
    )
def update_figures(direction_selector, is_internal_selector):

    int_colors = ['rgba(0, 100, 220, .8)','rgba(220, 0, 0, .8)']
    dir_colors = ['rgba(0, 150, 0, .8)','rgba(220, 220, 0, .8)']

    # Для набора №1

    direction = df.query('direction == @direction_selector')

    calls_by_date = direction.groupby(['direction','date_agg']).agg(
        {'call_duration':'sum'}).reset_index().rename(
            columns = {'call_duration':'duration_sum'})

    call_durations = []
    direction_types = direction['direction'].unique()
    direction_names = ['Исходящие', 'Входящие']

    for dir_index in range(len(direction_types)):
        call_direction = direction_types[dir_index]
        if call_direction == 'in':
            color=int_colors[1]
        else:
            color=int_colors[0]
        current = calls_by_date.query('direction == @call_direction')
        call_durations += [go.Scatter(x = current['date_agg'],
                            y = current['duration_sum'],
                            mode = 'lines',
                            stackgroup = 'one',
                            marker_color=color,
                            name = direction_names[dir_index]
                            )]

    pie_is_internal_calls = [go.Pie(labels = ['Внешние', 'Внутренние'],
                        values = direction['internal'].value_counts(),
                        name = 'Внутренние/внешние звонки',
                        marker = dict(colors=dir_colors)
                        )]

    # Для набора №2

    is_internal = df.query('internal == @is_internal_selector')

    calls_by_day = is_internal.groupby(['internal','date_agg']).agg(
        {'user_id':'count'}).reset_index().rename(columns = {'user_id':'calls_count'})
   
    calls_per_day = []
    internal_types = calls_by_day['internal'].unique()
    internal_names = ['Внешние','Внутренние']

    for int_index in range(len(internal_types)):
        call_intern = internal_types[int_index]
        if call_intern == 'True':
            color=dir_colors[1]
        else:
            color=dir_colors[0]
        current = calls_by_day.query('internal == @call_intern')
        calls_per_day += [go.Scatter(x = current['date_agg'],
                            y = current['calls_count'],
                            mode = 'lines',
                            stackgroup = 'one',
                            marker_color=color,
                            name = internal_names[int_index],
                            )]
    
    pie_in_out_calls = [go.Pie(labels = ['Исходящие', 'Входящие'],
                        values = is_internal['direction'].value_counts(),
                        name = 'Входящие/исходящие звонки',
                        marker = dict(colors=int_colors)
                        )]

    return ({
            'data': call_durations,
            'layout': go.Layout(xaxis = {'title': 'дата'},
                                        yaxis = {'title': 'длительность'})
                },
                {
            'data': pie_is_internal_calls,
            'layout': go.Layout()
                },
                {
            'data': calls_per_day,
            'layout': go.Layout(xaxis = {'title': 'дата'},
                                        yaxis = {'title': 'количество'})
                },
                {
            'data': pie_in_out_calls,
            'layout': go.Layout()
                },
    )

if __name__ == '__main__':
    app.run_server(debug = True, host='0.0.0.0')