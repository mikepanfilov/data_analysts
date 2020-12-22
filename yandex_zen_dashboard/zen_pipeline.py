#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import getopt
import pandas as pd
from sqlalchemy import create_engine

if __name__ == "__main__":

    # Задаем опции скрипта
    unixOptions = "s:e:"
    gnuOptions = ["start_dt=", "end_dt="]

    fullCmdArguments = sys.argv
    argumentList = fullCmdArguments[1:]

    try:
        arguments, values = getopt.getopt(argumentList, unixOptions, gnuOptions)
    except getopt.error as err:

        print (str(err))
        sys.exit(2)

    # Присваиваем начальную и конечную дату для удобства наладки скрипта
    start_dt = '2019-09-24 18:00:00'
    end_dt = '2019-09-24 19:01:00'

    # Присваиваем новые значения, если таковые заданы из командной строки
    for currentArgument, currentValue in arguments:
        if currentArgument in ("-s", "--start_dt"):
            start_dt = currentValue
        elif currentArgument in ("-e", "--end_dt"):
            end_dt = currentValue

    # Подключаемся к БД
    print('Connecting to database...',end='')
    db_config = {'user': 'my_user',
                 'pwd': 'my_user_password',
                 'host': 'localhost',
                 'port': 5432,
                 'db': 'zen'}
    connection_string = 'postgresql://{}:{}@{}:{}/{}'.format(db_config['user'],
                                                             db_config['pwd'],
                                                             db_config['host'],
                                                             db_config['port'],
                                                             db_config['db'])

    print('OK')
    # Инициализируем БД
    print('Initializing database engine...',end='')
    engine = create_engine(connection_string)
    print('OK')

    # Запрашиваем данные за требуемый период
    print('Querying data period from {} to {}...'.format(start_dt, end_dt), end='')

    query = ''' SELECT event_id, age_segment, event, item_id, item_topic,
                item_type, source_id, source_topic, source_type,
                TO_TIMESTAMP(ts / 1000) AT TIME ZONE 'Etc/UTC' as dt, user_id
                FROM log_raw
                WHERE TO_TIMESTAMP(ts / 1000) AT TIME ZONE 'Etc/UTC' BETWEEN '{}'::TIMESTAMP AND '{}'::TIMESTAMP
            '''.format(start_dt, end_dt)
    print('OK')

    # Преобразуем в Pandas
    print('Converting to pandas and operating...', end='')
    raw = pd.io.sql.read_sql(query, con = engine)

    # Округлим значения времени до минут
    raw['dt'] = pd.to_datetime(raw['dt']).dt.round('min')

    # Произведем агрегацию по данным для датафрейма событий и преобразуем для вида SQL
    dash_visits = raw.groupby(['item_topic', 'source_topic', 'age_segment', 'dt']).agg({'event_id':'count'})
    dash_visits = dash_visits.rename(columns = {'event_id': 'visits'})
    dash_visits = dash_visits.fillna(0).reset_index()

    # То же для датафрейма воронок
    dash_engagement = raw.groupby(['dt','item_topic', 'event','age_segment']).agg({'user_id':'nunique'})
    dash_engagement = dash_engagement.rename(columns = {'user_id': 'unique_users'})
    dash_engagement = dash_engagement.fillna(0).reset_index()
    print('OK')

    # определим словарь агрегационных датафреймов
    print('Preparing, deleting and loading data to dash_visits and dash_engagement...', end='')
    tables = {'dash_visits': dash_visits, 
              'dash_engagement': dash_engagement}

    # сформируем цикл для удаления и заполнения таблиц в Postgres базе zen
    for table_name, table_data in tables.items():   

        query = '''
                  DELETE FROM {} WHERE dt BETWEEN '{}'::TIMESTAMP AND '{}'::TIMESTAMP
                '''.format(table_name, start_dt, end_dt)
        engine.execute(query)

        table_data.to_sql(name = table_name, con = engine, if_exists = 'append', index = False)
    print('OK')
    print('All done.')