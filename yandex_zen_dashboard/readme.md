Добрый день! Я - инструкция по запуску пайплайна и дашборда для Яндекс.Дзен.
Все команды выполнены на bash под Linux.

Работа выполнена на Яндекс.Облаке - работающая версия дашборда доступна по адресу http://84.201.181.144:8050/
До окончания проверки я не буду останавливать даш-сервер, так что вы можете использовать эту ссылку.

1) Базы данных:

Полный дамп базы данных находится в файле zen_database.dump (три таблички: log_raw, dash_visits, dash_engagement)
Дамп выполнен из PostgreSQL.
Определения таблиц: 

CREATE TABLE log_raw(event_id serial PRIMARY KEY,        
                     age_segment VARCHAR(128),
                     event VARCHAR(128),
                     item_id BIGINT,    
                     item_topic VARCHAR(128),
                     item_type VARCHAR(128),    
                     source_id BIGINT,     
                     source_topic VARCHAR(128),    
                     source_type VARCHAR(128),     
                     timestamp BIGINT,    
                     user_id BIGINT);

CREATE TABLE dash_visits(record_id serial PRIMARY KEY,       
                         item_topic VARCHAR(128),
                         source_topic VARCHAR(128),
                         age_segment VARCHAR(128),
                         dt TIMESTAMP,
                         visits INT);

CREATE TABLE dash_engagement(record_id serial PRIMARY KEY, 
                             dt TIMESTAMP,        
                             item_topic VARCHAR(128),     
                             event VARCHAR(128),    
                             age_segment VARCHAR(128),
                             unique_users BIGINT);


2) Пайплайн:

Для обновления данных запустите скрипт zen_pipeline.py (в команду заложен временной интервал с 18:00 до 19:00 24 сентября 2019 года):

python3 zen_pipeline.py --start_dt='2019-09-24 18:00:00' --end_dt='2019-09-24 19:00:00'

3) Настройка расписания:

Вот строчка для cron.
Расписание настроено на каждый день в 3:15 (для UTC-0, с рассчетом на запуск в Москве в 0:15):

15 3 * * * python3 -u -W ignore /home/mikepaf/zen_pipeline.py --start_dt='2019-09-24 18:00:00' --end_dt='2019-09-24 19:00:00' >> /home/my_user/zen_logs/zen_pipeline_$(date +\%Y -d "1 day ago").log 2>&1

4) Дашборд:

Скрипт дашборда расположен в файле zen_dash.py. Запустить его можно так же:

python3 zen_dash.py

Дашборд будет работать как на локальной машине по адресу localhost:8050 , так и с внешнего источника по адресу http://<ваш внешний IP>:8050

5) Презентация:

Презентация к проекту в файле zen_presentation.pdf

Дополнительных файлов потребоваться не должно.