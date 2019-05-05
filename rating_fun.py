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

# объективнеы данные о турнире в удобном формате для дальнейшей работы
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
    # сьтобцы с 14 по 17 содержат текстовую информацию
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

# вся нужная информация в одном месте
# 
def qv_stat(tourn_id, is_api, is_write):
    
    df=prep_tourn(tourn_id, is_api, is_write)
    qv=df[df.columns[19:]]
    
    # главное - не перепутать строки и столбцы
    qvt=qv.values.shape[1]
    teams=qv.values.shape[0]
    
    
    d=difficult(qv.values)
    
    qv_t=qv.T
    qv_t['qv_num']=qv_t.index
    qv_t['chr_rank']=range(1, len(qv_t)+1)
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
        1:"1. Очень простые",
        2:"2. Простые",
        3:"3. Сложные",
        4:"4. Очень сложные"

    }
    g['class_dif']=g['class_order'].map(ddict)
    
    t=qv_t.merge(g, 'left', on='class', suffixes=('_qv', '_avg'))
    
    
    
    return t

def d_graph(tourn_id, is_api, is_write):
    import plotly
    from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
    import plotly.graph_objs as go
    init_notebook_mode(connected=True)
    
    df=qv_stat(tourn_id, is_api, is_write)
    
    df=df[['dif_rank', 'difficult_qv', 'class']]
    df['c1']=np.where(df['class']==1.00,df['class']+1,0)
    df['c2']=np.where(df['class']==0.00,df['class']+1,0)
    df['c3']=np.where(df['class']==0.33,df['class']+1,0)
    df['c4']=np.where(df['class']==0.67,df['class']+1,0)

    trace1 = go.Scatter(
        x=df['dif_rank'],
        y=df['difficult_qv'],
        #fill='tozeroy',
        name='dif',
        marker=dict(
            color='rgb(0, 0, 250)'
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
    

def qv_graph(tourn_id, is_api, is_write):
    import plotly
    from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
    import plotly.graph_objs as go
    init_notebook_mode(connected=True)
    
    df=qv_stat(tourn_id, is_api, is_write)
    
    df=df[['chr_rank', 'difficult_qv']].sort_values(by='chr_rank')

    trace1 = go.Scatter(
        x=df['chr_rank'],
        y=df['difficult_qv'],
        #fill='tozeroy',
        name='dif',
        marker=dict(
            color='rgb(0, 0, 250)'
        )
    )


    data = [trace1]
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
    
def hist(df):
    import plotly
    from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
    import plotly.graph_objs as go
    init_notebook_mode(connected=True)
    

    trace1 = go.Bar(
        x=df['stack'],
        y=df['team_id'],
        #fill='tozeroy',
        name='dif',
        marker=dict(
            color='rgb(0, 0, 250)'
        )
    )


    data = [trace1]
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
        char=int(np.round(char,0))


    top=df.groupby('team_id').sum()[['questions_suc']].sort_values(by='questions_suc', ascending=False).reset_index()
    top['place']=top.index
    top['is_top']=np.where(top['place']<=char-1, 1,0)
    
    res=res.merge(top[['team_id', 'is_top']], 'left', on='team_id')
    
    return res

# определяем стиль команды по статистике вопросов
def style(g):
    smpl=g[g['class_dif']=='1. Очень простые']['mark'].values[0]+g[g['class_dif']=='2. Простые']['mark'].values[0]
    hrd=g[g['class_dif']=='3. Сложные']['mark'].values[0]+g[g['class_dif']=='4. Очень сложные']['mark'].values[0]
    tot=np.sum(g['mark'])

    if tot<6:
        res='Слабая'
    elif smpl > hrd:
        res='Техничная'
    elif smpl < hrd:
        res='Креативная'
    elif smpl < hrd:
        res='Стабильная'
    else:
        res='Нестабильная'
    return res

# считаем статистику по конкретной команде
def team_stat(df, team_id, tourn_stat, top_stat):
    w=df[df['team_id']==team_id][['class_dif', 'result']]
    team_stat=w.groupby(['class_dif']).agg(['sum', 'count']).reset_index()
    team_stat['share']=team_stat['result']['sum']/team_stat['result']['count']
    
    team_stat['score']=team_stat['result']['sum']
    team_stat['total']=team_stat['result']['count']
    
    del team_stat['result']
    
    team_stat=team_stat.merge(tourn_stat[['share', 'class_dif']], 'left', on='class_dif', suffixes=('', '_tourn'))
    team_stat=team_stat.merge(top_stat[['share', 'class_dif']], 'left', on='class_dif', suffixes=('', '_top'))
    team_stat['team_id']=team_id
    
    # оценка за игру на каждом классе вопросов
    team_stat['mark']=np.where(team_stat['share']>=team_stat['share_top'], 3, 
                            np.where(
                                       (
                                           team_stat['share']>=team_stat['share_tourn']
                                       )
                                         &
                                       (
                                           team_stat['share']<team_stat['share_top']
                                       )
                                       , 2, 
                                  1)
                              )
    team_stat['style']=style(team_stat)
    
    return team_stat

# рсчёт значений по всему турниру
def total_culc(tourn_id, is_api, is_write):
    
    df=full_stat(tourn_id, is_api, is_write)
    # считаем статистику по турниру в целом
    w=df[['class_dif', 'result']]
    tourn_stat=w.groupby(['class_dif']).agg(['sum', 'count']).reset_index()
    tourn_stat['share']=tourn_stat['result']['sum']/tourn_stat['result']['count']
    
    # считаем статистику по лучшим командам
    w=df[df['is_top']==1][['class_dif', 'result']]
    top_stat=w.groupby(['class_dif']).agg(['sum', 'count']).reset_index()
    top_stat['share']=top_stat['result']['sum']/top_stat['result']['count']
    
    
    teams_list=df['team_id'].drop_duplicates().values
    #teams_list=[6874]
    t=pd.DataFrame()
    tb=pd.DataFrame()
    for team_id in teams_list:
        tb=team_stat(df, team_id, tourn_stat, top_stat)
        t=pd.concat([t, tb])
    
    return t

# уровень 4: показываем живым людям
def show_team_in_tourn(tourn_id, team_id, is_api, is_write):
    stat=full_stat(tourn_id, is_api, is_write)
    mark=total_culc(tourn_id, is_api, is_write)
    
    t=stat[stat['team_id']==team_id]
    m=mark[mark['team_id']==team_id]
    
    print('Команда', t['current_name'].values[0], '(id=',  t['team_id'].values[0], ') ')
    print('на турнире ', t['name'].values[0], '(id=', t['tourn_id'].values[0],')')
    print('Тип турнира: ', t['type_name'].values[0])
    print('Участвовало команд:', t['teams'].values[0])
    print('Результат команды: ', t['questions_suc'].values[0], '/', t['questions_total'].values[0])
    print('Изменения рейтинга команды после турнира:', t['diff_bonus'].values[0])
    
    print('Стиль команды на турнире:', m['style'].values[0])
    m=m[['class_dif', 'score', 'total', 'mark']]
    
    print('Статистика по типам вопросов:')
    print(m.values[0][0], ':', m.values[0][1], '/', m.values[0][2], 'оценка: ', m.values[0][3])
    print(m.values[1][0], ':', m.values[1][1], '/', m.values[1][2], 'оценка: ', m.values[1][3])
    print(m.values[2][0], ':', m.values[2][1], '/', m.values[2][2], 'оценка: ', m.values[2][3])
    print(m.values[3][0], ':', m.values[3][1], '/', m.values[3][2], 'оценка: ', m.values[3][3])
    
    taken=t[t['result']==1].sort_values(by='difficult', ascending=False)
    failed=t[t['result']==0].sort_values(by='difficult', ascending=True)
    
    print('Номера самых простых невзятых вопросв:', failed['qv_num'].values[0:3])
    print('Номера самых сложных взятых вопросов:', taken['qv_num'].values[0:3]) 
    
    return mark[mark['team_id']==team_id]


def show_tourn(tourn_id, is_api, is_write):
    stat=full_stat(tourn_id, is_api, is_write)
    print('Турнир ', stat['name'].values[0], '(id=', stat['tourn_id'].values[0], stat['date_start'].values[0], ')')
    qv_graph(tourn_id, is_api, is_write)
    d_graph(tourn_id, is_api, is_write)
    
    dd=stat.groupby('team_id').mean()[['diff_bonus']].reset_index().sort_values(by='diff_bonus')
    dd['stack']=np.round(dd['diff_bonus']/100,0)*100
    
    h=dd.groupby('stack').agg('count').sort_values(by='stack').reset_index()
    
    hist(h)
    
    print('Средний бонус:', np.round(np.mean(dd['diff_bonus']),2))
    print('Медианный бонус',np.median(dd['diff_bonus']))
    from scipy import stats
    print('Мода бонуса', stats.mode(dd['diff_bonus'])[0][0])
    
    print('Корреляция факта с прогнозом по местам', 
          np.round(stats.pearsonr(stat['position'], stat['predicted_position'])[0],2)
         )
    
    

