# coding: utf-8
# Файл с функциями для работы с сайтом рейтинга

import numpy as np
import pandas as pd

# уровень: турнир


# функция возвращает данные по конкретному турниру
# там дофига всего - команды, города, рейтинги, большинство в читаемом виде
# но вот  повопросные нормально не достать
# не зависит от самописных функций
def get_tourn(tourn_id, is_api, is_write):
    # если нас попросили достать с сайта, используем API
    if is_api==True:
        # волшебная строчка - вытаскивает по api в формате json данные и пишет в датафрейм
        t_url='http://rating.chgk.info/api/tournaments/'+str(tourn_id)+'/list'
        d=pd.read_json(t_url)
    
    # иначе: читаем из файла
    else:
        d=d.read_json('data/tourn/'+str(tourn_id)+'.json')
    
    # если нас попросили, пишем в файл
    if is_write==True:
        d.to_json('data/tourn/'+str(tourn_id)+'.json')
    
    return d
        
    
    



# уровень команда-турнир





# уровень: команда






# уровень: сезон
