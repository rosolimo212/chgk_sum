# coding: utf-8

# Файл с функциями для работы с сайтом рейтинга
# Необхожимые импорты
import numpy as np
import pandas as pd


# Уровни функций: получение инофрмации с сайта рейтинга, обработка для удобства работы, "выская наука" и красивый вывод
# Уровени работы: команда на турнире, турнир, команда за период


# Уровень 1: взять с сайта рейтинга

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
    path='data/tourn/list'+str(tourn_id)+'.json'
    
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


def get_tourn_meta(tourn_id, is_api, is_write):
    d=pd.DataFrame()
    
    # волшебная строчка - вытаскивает по api в формате json данные и пишет в датафрейм
    t_url='http://rating.chgk.info/api/tournaments/'+str(tourn_id)+'/'
    # путь, куда писать и откуда читать
    path='data/tourn/meta_'+str(tourn_id)+'.json'
    
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

# Уровень 2: привести в удобный формат

# Функция делает из строки с расплюсовкой массив с результатами одной конкретной команды
def qv_from_mask(mask):
    qv=np.array([])
    # заменяем снятый вопрос на ноль
    mask=mask.replace('X', '0')
    for ch in mask:
        qv=np.append(qv,int(ch))   
    return qv

def prep_tourn(tourn_id, is_api, is_write):
    # получаем данные "как есть"
    df=get_tourn(tourn_id, is_api, is_write)
    meta=get_tourn_meta(tourn_id, is_api, is_write)[['idtournament', 'name', 'date_start', 'type_name', 'questions_total']]
    
    df.columns=['base_name', 'bonus_a', 'bonus_b', 'current_name', 'diff_bonus',
       'team_id', 'included_in_rating', 'mask', 'position',
       'predicted_position', 'questions_suc', 'tech_rating']
    
    # добавим важеные поля
    # id турнира
    df['tourn_id']=tourn_id
    # -1 если сыграли в минус, +1 если "в плюс"
    df['result']=np.sign(df['diff_bonus'])
    
    # подтянули мету про турнир в целом
    df=df.merge(meta, 'left', left_on='tourn_id', right_on='idtournament')
    
    df['teams']=len(df)
    
    # делаем нормальную расплюсовку
    # число вопросов в турнире
    numqv=df['questions_total'].values[0]
    
    # цикл по каждому вопросу
    for i in range(numqv):
        df['qv_'+str(i+1)]=df['mask'].apply(lambda x: qv_from_mask(x)[i])
    

        
    # уберём длиннубю ненужную строку    
    del df['mask']
    
    # приведём всё к целому типу
    r1=df.columns[4:14]
    r2=df.columns[17:]
    r=np.append(r1, r2)
    for col in r:
        df[col]=df[col].astype('int64')
    
    return df
    
    


