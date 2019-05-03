# coding: utf-8
# Файл с функциями для работы с сайтом рейтинга

import numpy as np
import pandas as pd

# уровень: турнир


# функция возвращает данные по конкретному турниру
# там дофига всего - команды, города, рейтинги, большинство в читаемом виде
# но вот  повопросные нормально не достать
# не зависит от самописных функций
# на входе id турнира, нужно ли брать данные с сайта (или файла)
# и нужно ли писать в файл
# на выходе pandas data frame
def get_tourn(tourn_id, is_api, is_write):
    d=pd.DataFrame()
    
    # волшебная строчка - вытаскивает по api в формате json данные и пишет в датафрейм
    t_url='http://rating.chgk.info/api/tournaments/'+str(tourn_id)+'/list'
    # путь, куда писать и откуда читать
    path='data/tourn/'+str(tourn_id)+'.json'
    
    # если нас попросили достать с сайта, используем API
    if is_api==True:
        d=pd.read_json(t_url)
    
    # иначе: читаем из файла
    else:
        d=pd.read_json(path)
    
    # если нас попросили, пишем в файл
    if is_write==True:
        d.to_json(path)
    
    return d

# выборка информации турнира
# зависит от get_tourn()
def get_tourn_result(tourn_id):
    gt=get_tourn(tourn_id)
    gt=gt[['idteam', 'current_name', 'diff_bonus']]
    gt['tourn_id']=tourn_id
    gt['result']=np.sign(gt['diff_bonus'])
    gt.columns=['team_id', 'name', 'diff_bonus', 'tourn_id', 'result']
    return gt   
    



# уровень команда-турнир

# функция возвращает результат данной команды в данном турнире 
# в формате +1-1+0 (сыграла "в плюс", "в минус" или "в ноль") с точки зрения рейтингового прогноза
# зависит от get_tourn()
def get_team_result(tourn_id, team_id):
    gt=get_tourn(tourn_id)
    bns=gt[gt['idteam']==team_id]['diff_bonus'].values[0]
    return np.sign(bns)


# вытаскивае расплюсовку команды в данном турнире в ненормализованном виде
def get_team(tourn_id, team_id, is_api, is_write):
    d=pd.DataFrame()
    
    # волшебная строчка - вытаскивает по api в формате json данные и пишет в датафрейм
    t_url='http://rating.chgk.info/api/tournaments/'+str(tourn_id)+'/results/'+str(team_id)
    # путь, куда писать и откуда читать
    path='data/team_tourn/s_'+str(tourn_id)+'-'+str(team_id)+'.json'
    
    # если нас попросили достать с сайта, используем API
    if is_api==True:
        d=pd.read_json(t_url)
    
    # иначе: читаем из файла
    else:
        d=pd.read_json(path)
    
    # если нас попросили, пишем в файл
    if is_write==True:
        d.to_json(path)
    
    return d


# функция, которая возвращает DatFrame строку: повопросные резульататы команды team_id в турнире tourn_id
# зависит от get_team()
def get_team_from_tourn(tourn_id, team_id, is_api, is_write):
    d=get_team(tourn_id, team_id, is_api, is_write)
    
    # лично меня бесит разбивка повопросных результатов по турам и ненормализованный вид таблиц из-за этого
    # в связи с этим начинаю некоторые танцы с бубном
    
    num_t=max(d['tour'])     # Зафиксировали число туров 
    num_qv=len(d['mask'][0]) # зафиксировали число вопросов в туре
    
    # TO DO: проверить, что бывает с турнирами, где в турах разное число вопросов
    
    rplus=list(d['mask'])
    # mask - это поле, в котором лежит список с ответами команды в туре 
    # в формате 1 (взяытй), 0 (не взятый), X - снятый (зачем?)
    # формат не очень удобный, но в экспоте с турниром вообще не распаршивается
    
    
    # ниже вытаскиваем из mask данные каждого вопроса и создаём для него свой столбец в DataFrame
    
    # TO DO: сделатиь через numpy-массивы
    tt=0 # Счётчик вопроса, начинаем с 1
    s_l=[]  # Список с заголовком столбца
    r_l=[]  # Список со значением столбца
    
    for j in range(num_t):
        for i in range(num_qv):
            tt=tt+1
            r_l.append(rplus[j][i])
            s_l.append('qv'+str(tt))
    
    # Через словарь записываем всё в DataFrame. Наверняка можно сделаь проще
    res={} 
    res = {'tourn_id': tourn_id, 'team_id': team_id} # поля с парамерами команды и турнира появляются в пустом словаре
    for i in range(len(s_l)):
        res.update({s_l[i]:r_l[i]})   # в цикле добавляем по одной записи на каждый вопрос, это не должно быть долго
        
    d=pd.DataFrame([res], columns=res.keys())
    d=d.replace('X', 0)  # X - это снятый вопрос
    d=d.astype('int64')
    
    return d

# функция выводит расплюсовку всех команд турнира
# функция дублирует поле mask в параметрах турнира, но его нельзя корректно загрузить в pandas
# для работы нужны get_tourn() и get_team_from_tourn()
def get_tourn_plus(tourn_id):
    d=pd.DataFrame()
    
    # волшебная строчка - вытаскивает по api в формате json данные и пишет в датафрейм
    t_url=''
    # путь, куда писать и откуда читать
    path='data/'+'.json'
    
    # если нас попросили достать с сайта, используем API
    if is_api==True:
        d=
    
    # иначе: читаем из файла
    else:
        d=
    
    # если нас попросили, пишем в файл
    if is_write==True:
        d.to_json(path)
    
    
    
    

    
        
        



# уровень: команда






# уровень: сезон
