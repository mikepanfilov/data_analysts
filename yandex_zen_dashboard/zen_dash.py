2#!/usr/bin/python
# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from sqlalchemy import create_engine

#Подключимся к базе данных
print('Connecting to database...', end='')
db_config = {'user': 'my_user',
            'pwd': 'my_user_password',
            'host': 'localhost',
            'port': 5432,
            'db': 'zen'}
engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(db_config['user'],
                                                           db_config['pwd'],
                                                           db_config['host'],
                                                           db_config['port'],
                                                           db_config['db']))

print('ОК')

# Запросим данные из БД
print('Querying data from dash_visits and dash_engagement...', end='')

query = '''
            SELECT * FROM dash_visits
        '''
dash_visits = pd.io.sql.read_sql(query, con = engine)
dash_visits['dt'] = pd.to_datetime(dash_visits['dt'])

query = '''
            SELECT * FROM dash_engagement
        '''
dash_engagement = pd.io.sql.read_sql(query, con = engine)
dash_engagement['dt'] = pd.to_datetime(dash_engagement['dt'])

print('OK')


# Формируем шаблон
print('Making layout...', end='')

# Описание дашборда
dash_note = '''
            Этот дашборд показывает статистику поведения в сервисе Яндекс.Дзен. 
            Используйте настройки даты и времени, настройте фильтр возрастных категорий и фильтр тем карточек.
            '''

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(children=[

    # Формируем html
    html.H2(children = 'Яндекс.Дзен : cтатистика'),
    html.Br(),
    html.Label(dash_note),
    html.Br(),
    html.Div([
        html.Div([
            html.Label('Фильтр даты:'),
            dcc.DatePickerRange(
                start_date = dash_visits['dt'].min(),
                end_date = dash_visits['dt'].max(),
                display_format = 'YYYY-MM-DD',
                id = 'dt_selector',       
            ),
            html.Br(),
            html.Br(),
            html.Label('Возрастные категории:'),
            dcc.Dropdown(
                options = [{'label': x, 'value': x} for x in dash_visits['age_segment'].unique()],
                value = dash_visits['age_segment'].unique().tolist(),
                style = {'width':'80%'},
                multi = True,
                id = 'age-dropdown'
            ),
            html.Br(),   
        ], className = 'six columns'),
        
        
        html.Div([
            html.Label('Темы карточек:'),
            dcc.Dropdown(
                options = [{'label': x, 'value': x} for x in dash_visits['item_topic'].unique()],
                value = dash_visits['item_topic'].unique().tolist(),
                multi = True,
                id = 'item-topic-dropdown'
            ),
            html.Br(),
        ], className = 'six columns'),
    ], className='row'),

    
    html.Div([    
        html.Div([
            html.Label('График истории событий по темам карточек:'),
            dcc.Graph(
                id = 'history-absolute-visits',
                style = {'height':'50vw'}
            ),           
        ], className = 'six columns'),
        
        html.Div([
            html.Label('График разбивки событий по темам источников:'),
            dcc.Graph(
                id = 'pie-visits',
                style = {'height':'25vw'}
            ),
            html.Br(),
            html.Label('График средней глубины взаимодействия:'),
            dcc.Graph(
                id = 'engagement-graph',
                style = {'height':'25vw'},
            ),
        ], className = 'six columns'),
    ], className='row'),
])
print('OK')

# Описываем логику
print('Working on logic...', end='')
@app.callback(
    [Output('history-absolute-visits','figure'), 
    Output('pie-visits','figure'), Output('engagement-graph','figure'),],
    
    [Input('item-topic-dropdown','value'), 
    Input('age-dropdown','value'), 
    Input('dt_selector','start_date'), Input('dt_selector','end_date'),]
    )
def update_figures(selected_item_topics,selected_ages,start_date,end_date):
    
    # Датафрейм для истории событий:
    report_dv_i = dash_visits.query('item_topic.isin(@selected_item_topics) and \
                                    dt >= @start_date and dt <= @end_date \
                                    and age_segment.isin(@selected_ages)')
    
    report_dv_i = report_dv_i.groupby(['item_topic','dt']).agg({'visits':'sum'}).reset_index()

    # Датафрейм для разбивки по темам источников:
    report_dv_s = dash_visits.query('item_topic.isin(@selected_item_topics) and \
                                    dt >= @start_date and dt <= @end_date \
                                    and age_segment.isin(@selected_ages)')

    report_dv_s = report_dv_s.groupby(['source_topic']).agg({'visits':'sum'}).reset_index()

    # Датафрейм для графика воронки взаимодействия:
    report_de = dash_engagement.query('item_topic.isin(@selected_item_topics) and \
                                    dt >= @start_date and dt <= @end_date \
                                    and age_segment.isin(@selected_ages)')
    report_de = report_de.groupby(['event']).agg({'unique_users':'mean'}).reset_index()
    report_de = report_de.rename(columns = {'unique_users':'avg_unique_users'})
    report_de = report_de.sort_values(by='avg_unique_users', ascending=False).reset_index(drop=True)
    
    # Рассчет доли пользователей относительно показов:
    try:
        base = report_de['avg_unique_users'][0]
        pct_list = []
        for row in report_de['avg_unique_users']:
            pct_list.append(round(row/base,2))
        report_de['avg_unique_users'] = pct_list
    except:
        pass
        
    
    # Отрисовка
    history_absolute_visits = []
    for topic in report_dv_i['item_topic'].unique():
        current = report_dv_i.query('item_topic == @topic')
        history_absolute_visits += [go.Scatter(x=current['dt'], 
                                                y=current['visits'],
                                                mode = 'lines',
                                                stackgroup = 'one',
                                                name = topic)]
   
    pie_visits = [go.Pie(labels = report_dv_s['source_topic'],
                        values = report_dv_s['visits'],
                        name = 'Темы источников')]

    engagement_graph = [go.Bar(x = report_de['event'],
        y = report_de['avg_unique_users'],
                        text=report_de['avg_unique_users'],
                        texttemplate='%{text:.0%}',
                        textposition='auto')]


    # Вывод
    return (
            {
                'data': history_absolute_visits,
                'layout': go.Layout(xaxis = {'title': 'Время'},
                                    yaxis = {'title': 'Кол-во визитов'})
             },
            {
                'data': pie_visits,
                'layout': go.Layout()
             },           
            {
                'data': engagement_graph,
                'layout': go.Layout()
             },        
  )

print('OK')

# Запуск сервера
print('Running server...')
if __name__ == '__main__':
    app.run_server(debug = True, host='0.0.0.0')
print('Server switched off. Goodbye!')