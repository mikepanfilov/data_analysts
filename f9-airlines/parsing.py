# Анализ для компании «F9» — это российская авиакомпания, 
# выполняющая внутренние пассажирские авиаперевозки. 
# Сотни перелётов каждый день. Важно понять предпочтения пользователей, 
# покупающих билеты на те или иные направления.

# Необходимо парсер для сбора с сайта данных о 11 крупнейших фестивалях 2018 года. 
# Сохраните данные в датафрейм festivals и выведите на экран.
# Ссылка на сайт: 
# https://code.s3.yandex.net/learning-materials/data-analyst/festival_news/index.html

import requests
from bs4 import BeautifulSoup
import pandas as pd

URL = 'https://code.s3.yandex.net/learning-materials/data-analyst/festival_news/index.html'
req = requests.get(URL)

soup = BeautifulSoup(req.text, 'lxml')

table = soup.find("table", attrs={"id":"best_festivals"})

f_columns = []
for row in table.find_all('th'):
    f_columns.append(row.text)

f_content = []
for row in table.find_all('tr'):
    if not row.find_all('th'):
        f_content.append([element.text for element in row.find_all('td')])
        
festivals = pd.DataFrame(f_content, columns=f_columns)

print(festivals)