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
        d=pd.read_json(t_url, dtype={'mask':'str'})
    
    # иначе: читаем из файла
    else:
        d=pd.read_json(path, dtype={'mask':'str'})
    
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
    
# Уровень 3: высокая наука

# расчёт слоэности каждого вопроса
# на вход подаём numpy-массив (строки - команды, столбцы - вопросы)
# на выходе массив сложностей
def difficult(table):
    
    # главное - не перепутать строки и столбцы
    qv=table.shape[1]
    teams=table.shape[0]
    
    # сложность - доля команд, которые не взяли вопрос
    # у "гроба" сложность 1, у "гайки" - 0
    d=(teams-np.sum(table, axis=0))/teams
    
    return d


def qv_stat(tourn_id, is_api, is_write):
    
    df=prep_tourn(tourn_id, is_api, is_write)
    qv=df[df.columns[19:]]
    
    # главное - не перепутать строки и столбцы
    qvt=qv.values.shape[1]
    teams=qv.values.shape[0]
    
    d=difficult(qv.values)
    
    qv_t=qv.T
    qv_t['qv_num']=qv_t.index
    qv_t['teams']=teams
    qv_t['questions']=qvt
    qv_t['difficult']=d
    qv_t['share']=1-qv_t['difficult']
    
    from scipy.stats import rankdata
    qv_t['dif_rank']=qvt-rankdata(qv_t['difficult'], method='ordinal')
    
    
    # сортировка в порядке убывания сложности
    # по идее она не должна влиять на результат кластеризации, хотя кто его знает
    qv_t=qv_t.sort_values(by='dif_rank')
    
    from sklearn.cluster import KMeans
    X=qv_t[['questions', 'difficult']].values  # бахнули число вопросов, так как стандартный интерфейс K-means двумерный
    kmeans = KMeans(n_clusters=4, random_state=20).fit(X)  # 4 кластера - не догма, но выглядит разумно
    
    qv_t['class']=np.round((kmeans.labels_)/max(kmeans.labels_),2)
    # нормировка лейблов:
    # во-первых, графики на одной оси,
    # во-вторых в случае изменения числа кластеров у старшего всё равно будет 1 
    
    g=qv_t.groupby('class').agg({ 'difficult': np.mean})
    g['class_order']=rankdata(g['difficult'], method='ordinal')
    ddict={
        1:"1. Очень простой",
        2:"2. Простой",
        3:"3. Сложный",
        4:"4. Очень сложный"

    }
    g['class_dif']=g['class_order'].map(ddict)
    
    t=qv_t.merge(g, 'left', on='class', suffixes=('_qv', '_avg'))
    
    
    
    return t

def d_graph(df):
    import plotly
    from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
    import plotly.graph_objs as go
    init_notebook_mode(connected=True)
    
    df=df[['dif_rank', 'difficult', 'class']]
    df['c1']=np.where(df['class']==1.00,df['class']+1,0)
    df['c2']=np.where(df['class']==0.00,df['class']+1,0)
    df['c3']=np.where(df['class']==0.33,df['class']+1,0)
    df['c4']=np.where(df['class']==0.67,df['class']+1,0)

    trace1 = go.Scatter(
        x=df['dif_rank'],
        y=df['difficult'],
        #fill='tozeroy',
        name='dif',
        marker=dict(
            color='rgb(250, 250, 250)'
        )
    )
    trace2 = go.Scatter(
        x=df['dif_rank'],
        y=df['c1'],
        name='class 1',
        fill='tonexty',
        opacity= 0.2,
        marker=dict(
            color='rgb(50, 103, 189)'
        )
    )
    trace3 = go.Scatter(
        x=df['dif_rank'],
        y=df['c2'],
        name='class 2',
        fill='tonexty',
        opacity= 0.2,
        marker=dict(
            color='rgb(148, 0, 189)'
        )
    )
    trace4 = go.Scatter(
        x=df['dif_rank'],
        y=df['c3'],
        name='class 3',
        fill='tonexty',
        opacity= 0.2,
        marker=dict(
            color='rgb(148, 103, 0)'
        )
    )
    trace5 = go.Scatter(
        x=df['dif_rank'],
        y=df['c4'],
        name='class 4',
        fill='tonexty',
        opacity= 0.2,
        marker=dict(
            color='rgb(150, 220, 50)'
        )
    )

    data = [trace2, trace3, trace4, trace5, trace1]
    layout = go.Layout(
        title='Dif class',
        yaxis=dict(
            title='',
            rangemode='tozero'
        ),
        yaxis2=dict(
            title='',
            titlefont=dict(
                color='rgb(148, 103, 189)'
            ),
            tickfont=dict(
                color='rgb(148, 103, 189)'
            ),
            overlaying='y',
            side='right',
            rangemode='tozero'
        )
    )
    fig = go.Figure(data=data, layout=layout)
    iplot(fig, show_link=False)
    
    return df

# функция для сбора всей важной информации о туирнире в нормализованном виде
# дальше только слайсить и группировать
def full_stat(tourn_id, is_api, is_write):
    # данные о турнире
    df=prep_tourn(tourn_id, is_api, is_write)
    
    # данные о сложности вопросов
    q=qv_stat(tourn_id, is_api, is_write)
    
    # список названий полей с номерами вопросов
    ql=df.columns[19:]
    # список названий остальных полей
    fl=df.columns[:19]

    # приводим в третью нормализованную форму
    norm=pd.melt(df, id_vars=fl, value_vars=ql)
    
    # берём только нужные поля
    q=q[['qv_num', 'difficult_qv', 'share', 'dif_rank', 'class', 'difficult_avg', 'class_order', 'class_dif']]
    
    # финальный джойн
    res=norm.merge(q, 'left', left_on='variable', right_on='qv_num')
    
    del res['variable']
    
    res.columns=['base_name', 'bonus_a', 'bonus_b', 'current_name', 'diff_bonus',
       'team_id', 'included_in_rating', 'position', 'predicted_position',
       'questions_suc', 'tech_rating', 'tourn_id', 'rating_result', 'idtournament',
       'name', 'date_start', 'type_name', 'questions_total', 'teams', 'result', 
       'qv_num', 'difficult', 'share', 'dif_rank', 'class', 'difficult_avg',
       'class_order', 'class_dif']
    
    teams=res['teams'].values[0]
    char=teams*0.1
    if teams<30:
        char=3
    else:
        char=int(np.round(teams*0.1,0))


    top=df.groupby('team_id').sum()[['questions_suc']].sort_values(by='questions_suc', ascending=False).reset_index()
    top['place']=top.index
    top['is_top']=np.where(top['place']<=char-1, 1,0)
    
    res=res.merge(top[['team_id', 'is_top']], 'left', on='team_id')
    
    
    return res
