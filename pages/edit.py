import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table,callback
from dash.dependencies import Input, Output, State, ALL
from matplotlib import category
import pandas as pd
import re
from .core import write_db,node_calculation
from node import quality_node, quality_activity, quality_implementation, quality_requirement
from task import task
import plotly.graph_objs as go
import sqlite3
from dash.exceptions import PreventUpdate
import json
import psycopg2
#Excelのファイル名とシート名
e_base = '保守性_DB.xlsx'
e_square = 'SQuaRE'
e_maintainability = 'maintainability'
e_architecture = 'architecture'
e_request = 'request'


#データの読み取り
df_square = pd.read_excel(e_base, sheet_name=[e_square])
df_maintainability = pd.read_excel(e_base, sheet_name=[e_maintainability])
df_architecture = pd.read_excel(e_base, sheet_name=[e_architecture])
df_request = pd.read_excel(e_base, sheet_name=[e_request])


# グラフ作成
def make_data(mae, now):
  labels = ['達成', '未達成']
  previous = [now, 100 - now]
  current = [mae, 100 - mae]
  colors = ['#FF9999', 'rgb(255, 0, 0)']
  trace_previous = go.Pie(
    labels=labels,
    values=previous,
    sort=False,
    hole=0,
    textinfo='none',  
    hoverinfo='none',
    marker=dict(colors=[colors[1], 'rgba(0,0,0,0)'],
                line=dict(color='black', width=1))
    )
  trace_current = go.Pie(
    labels=labels,
    values=current,
    hole=0,
    sort=False,
    textinfo='none',  
    hoverinfo='none',
    marker=dict(colors=[colors[0], 'rgba(0,0,0,0)'],
                line=dict(color='black', width=1))
    )
  figure = go.Figure(data=[trace_previous, trace_current])
  figure.update_layout(
    showlegend=False,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(size=9),
    autosize=False,
    height=37,
    width=37,
    margin=dict(l=1, r=1, t=1, b=1),
    )
  return figure


# 貢献度％計算
tree_contribution = []
tree_name = []
def calculate_contribution_percentage(node, x=None):
  global tree_contribution, tree_name
  if node is None:
    return None
  elif type(node) != str:
    if x == None:
      tree_name = []
      tree_contribution = []
    if node.children is not None:
      total_contribution = 0
      child_contribution = []
      child_name = []
      for child in node.children:
        total_contribution += child.contribution
        child_name += [child.id]
        child_contribution += [child.contribution]
      for x, y in zip(child_name, child_contribution):
        tree_name += [x]
        tree_contribution += [round(y/total_contribution*100)]
      for child in node.children:
        calculate_contribution_percentage(child, x=1)
    return 0
  else:
    for x, y in zip(tree_name, tree_contribution):
      if x == node:
        return y


# 貢献度を数字に変換
def chenge_int(x):
  if x == 'H':
    return int(3)
  elif x == 'M':
    return int(2)
  elif x == 'L':
    return int(1)
  else:
    return int(0)

# 文の改行処理
def insert_line_breaks(text):
  delimiters = ['[', '○', '×', '・', '①', '②']
  for delimiter in delimiters:
    text = text.replace(delimiter, '￥￥' + delimiter)
  delimiters = ['￥￥']
  pattern = '|'.join(map(re.escape, delimiters))
  parts = re.split(pattern, text)
  if parts[0] == '':
    parts.pop(0)
  for i in range(len(parts) - 1):
    parts.insert(2 * i + 1, html.Br())
  return parts


# 貢献度を検索
def search(category_num, node):
    conn = sqlite3.connect('QC_DB.db')
    cursor = conn.cursor()
    # テーブルからデータを取得
    cursor.execute(
        'SELECT importance FROM subcategories WHERE category_id = ? AND third_name = ?', (category_num, node))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    re_data = data[0]
    return chenge_int(re_data[0])

# カテゴリのプルダウンの作成
def dropdown_sub(category_num, SQuaRE_name):
  options = []
  list = ('H', 'M', 'L', 'N')
  color_list = ('red', 'orange', 'LightGreen', 'MediumTurqoise')
  conn = sqlite3.connect('QC_DB.db')
  cursor = conn.cursor()
  cursor.execute('SELECT third_name, importance FROM subcategories WHERE category_id = ? AND second_name = ?', (category_num,SQuaRE_name,))
  data = cursor.fetchall()
  cursor.close()
  conn.close()
  x = 0
  for i in list:
    for num in data:
      if num[1] == i:
        options.append({'label': html.Div(num[0], style={'color': color_list[x], 'font-size': 15}),'value': num[0]})
    x = x+1
  return options


# 要求文の作成
def make_request(node, node_data):
  options = []
  new_options = []
  for row in df_request[e_request].values:
    if row[1] == node:
      options += [{'label': row[2],'value': row[2]}]
  new_options = [dict(t) for t in {tuple(d.items()) for d in options}]
  if node_data.children is not None:
    for children in node_data.children:
      for row in df_request[e_request].values:
        if row[3] == children.id or row[7] == children.id:
          for option in new_options:
            label = option['label']
            if label == row[2]:
              option['disabled'] = True
      if children.id == '修正量の低減':
        for row_2 in df_request[e_request].values:
          if row_2[8] == 2:
            for option in new_options:
              label = option['label']
              if label == row_2[2]:
                option['disabled'] = True
          
  return new_options


#各名称の作成
def make_adovaic_node(node):
  options = []
  options += [
        {
          'label': html.Div('<品質実現>', style={'font-size': 15}),
          'value': 0,
          'disabled': True
          }
        ]
  for row in df_request[e_request].values:
    if row[2] == node:
      for ri in df_architecture[e_architecture].values:
        if ri[3] == row[7]:
          options += [
            {
              'label': html.Div(ri[3], style={'font-size': 15}),
              'value': ri[3]
              }
            ]
  options += [
    {
      'label': html.Div('<品質活動>', style={'font-size': 15}),
      'value': 0,
      'disabled': True
      }
    ]
  for row in df_request[e_request].values:
    if row[2] == node:
      options += [
        {
          'label': html.Div(row[3], style={'font-size': 15}),
          'value': row[3]
          }
        ]
  return options


# 各名称の作成_子供あり
def make_adovaic_node_children(node, node_data):
  options = []
  for row in df_request[e_request].values:
    if row[3] == node or row[7] == node:
      options += [{'label': html.Div('<品質実現>', style={'font-size': 15}),'value': 0,'disabled': True}]
      for ri in df_architecture[e_architecture].values:
        if ri[3] == row[7]:
          options += [{'label': html.Div(ri[3], style={'font-size': 15}),'value': ri[3]}]
      options += [{'label': html.Div('<品質活動>', style={'font-size': 15}),'value': 0,'disabled': True}]
      options += [{'label': html.Div(row[3], style={'font-size': 15}),'value': row[3]}]
  for option in options:
    value = option['value']
    if value == node:
      option['disabled'] = True
  if node_data.children is not None:
    for option in options:
      value = option['value']
      for children in node_data.children:
        if value == children.id:
          option['disabled'] = True
 
  return options

def make_adovaic_node_children_1(node_data):
  options = []
  new_options = []
  for row in df_request[e_request].values:
    if row[8] == 2:
      options += [{'label': row[2],'value': row[2]}]
  new_options = [dict(t) for t in {tuple(d.items()) for d in options}]
  if node_data.children is not None:
    for children in node_data.children:
      for row in df_request[e_request].values:
        if row[3] == children.id or row[7] == children.id:
          for option in new_options:
            label = option['label']
            if label == row[2]:
              option['disabled'] = True
  return new_options

# 貢献度のプルダウンデータ
def select_data():
  data = [
    {'label': '貢献度：高', 'value': '3'},
    {'label': '貢献度：中', 'value': '2'},
    {'label': '貢献度：低', 'value': '1'},
    {'label': '貢献度：不要', 'value': '0'}
    ]
  return data

#貢献度保存用変数
save_percent = []
def update_save_percent(num, text):
    global save_percent
    
    # 既存のtextがある場合は値を更新
    for item in save_percent:
        if item[1] == text:
            item[0] = num
            return
    
    # 既存のtextがない場合は新しい要素を追加
    save_percent.append([num, text])


#左の作成
def message_display(node,pid):
  if node is None:
    return None
  else:
    children = []
    for row in df_architecture[e_architecture].values:
      if row[3] == node:
        children = [
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<基本戦略>',style={'fontSize': 15,'fontWeight': 'bold'})
                  ],
                className='text-center',
                width=2,
                align='center'),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[1]),id='ar_base')
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<個別戦略>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center'),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[2]),id='ar_in'),
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<説明>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center',
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[4]),id='ar_exa')
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<前提条件>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[5]),id='ar_tec'),
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<実現手段一覧>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[6]),id='ar_tec'),
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<実現手段入力>',style={'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'}),
                  ],
                className='text-center',
                width=2,
                align='center',
                ),
              dbc.Col(
                [
                  dbc.Input(id={'type': 'input','index': 're_'+row[3]},
                            type='text',
                            value=write_db.check_description(pid, row[3]),
                            placeholder='手法を記載してください...',
                            )
                  ]
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<貢献度入力>',style={'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  dcc.Dropdown(
                    options=select_data(),
                    id={'type': 'dropdown','index': 're_'+row[3]},
                    placeholder='貢献度...',
                    value=write_db.check_contribution(pid, row[3])
                    )
                  ],
                width=8,
                ),
              dbc.Col(
                [
                  html.Button(
                    '更新',
                    id={'type': 'button','index': 're_'+row[3]},
                    style={'background-color': 'red'}
                    )
                  ],
                width=2
                )
              ]
            )
          ]
        return children
    for row in df_request[e_request].values:
      if row[3] == node:
        children = [
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<説明>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[4]),id='re_exa'),
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<測定機能>',style={'fontSize': 15,'fontWeight': 'bold'})
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[5]),id='re_ex')
                  ],
                width=5
                ),
              dbc.Col(
                [
                  dbc.Label('<測定A>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  dbc.Label('<測定B>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                width=1
                ),
              dbc.Col(                                
                      [
                        html.P('他研究A',id='re_a'),
                        html.P('他研究B',id='re_b')
                        ],
                      width=4
                      ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(  
                [   
                  dbc.Label('<Xの許容範囲>',style={'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'})
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  dcc.RangeSlider(
                    0.00,
                    1.00,
                    value=write_db.check_scope(pid, row[3]),
                    id={'type': 'input','index': 're_'+row[3]},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                    marks={
                      0: {'label': '0', 'style': {'color': '#77b0b1'}},
                      0.20: {'label': '0.2'},
                      0.40: {'label': '0.4'},
                      0.60: {'label': '0.6'},
                      0.80: {'label': '0.8'},
                      1: {'label': '1', 'style': {'color': '#f50'}}
                      }
                    )
                  ],
                width=8
                ),
              html.Br(),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<貢献度入力>',style={'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  dcc.Dropdown(
                    options=select_data(),
                    id={'type': 'dropdown','index': 're_'+row[3]},
                    placeholder='貢献度...',
                    value=write_db.check_contribution(pid, row[3])
                    )
                  ],
                width=7
                ),
              dbc.Col(
                [
                  html.Button(
                    '更新',
                    id={'type': 'button','index': 're_'+row[3]},
                    style={'background-color': 'red'}
                    )
                  ],
                width=2
                )
              ]
            )
          ]
        break
    return children


#品質状態モデル表示の画面
def tree_display(node, category, pid,indent=''):
  if node is None:
    return None
  else:
    if node.type != 'QRM':
      aim_node = write_db.check_node(pid,node.id)
      before = write_db.check_achievement_old(pid, node.id)
      now = aim_node[6]
      com = '達成:'+str(now)+'%'
    if node.type == 'REQ':
      if node.id == '保守性':
        num = calculate_contribution_percentage(node.id)
        update_save_percent(num, node.id)
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node)) + '%' + ']', style={'display': 'none', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('品質要求', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                dbc.Popover(dbc.RadioItems(options=dropdown_sub(category, node.id),
                                           id={'type': 'radio', 'index': node.id}),
                            target={'type': 'button','index': node.id},
                            body=True,
                            trigger='hover'),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}),
                ]
              )
            ],
          open=True
          )
      else:
        num = calculate_contribution_percentage(node.id)
        update_save_percent(num, node.id)
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('品質要求', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                dbc.Popover(dbc.RadioItems(options=make_request(node.id, node),
                                           id={'type': 'radio', 'index': node.id}),
                            target={'type': 'button','index': node.id},
                            body=True,
                            trigger='hover',
                            ),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              )
            ],
          open=True,
          style={'margin-left': '15px'}
          )
    elif node.type == 'IMP':
      ver = 0
      for row in df_request[e_request].values:
        if row[7] == node.id:
          ver = row[8]
          text = row[2]
          break
      if ver == 1 :
        num = calculate_contribution_percentage(node.id)
        update_save_percent(num, text)
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('PQ要求文:', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                dbc.Popover(dbc.RadioItems(options=make_adovaic_node_children(node.id, node),
                                           id={'type': 'radio','index': node.id}),
                            id='popover',
                          target={'type': 'button','index': 'ex'+node.id},
                          body=True,
                          trigger='hover',
                          ),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              )
            ],
          open=True,
          style={'margin-left': '15px'}
          )
        tree.children.append(
          html.Details(
            [
              html.Summary(
                [
                  html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                  html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                  html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                  html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                  html.P(dcc.Graph(
                    figure=make_data(before, now),
                    config={'displayModeBar': False}
                    ),
                         style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                         )
                  ]
                ),
              html.P('実現手法：' + str(node.other),style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
              ],
            style={'margin-left': '15px', 'marginBottom': '5px'}
            )
          )
      elif ver == 2:
        num = row[9]
        update_save_percent(num, text)
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[＋'+row[9]+']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('PQ要求文:', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                dbc.Popover(dbc.RadioItems(options=make_adovaic_node_children(node.id, node),
                                           id={'type': 'radio','index': node.id}),
                            id='popover',
                          target={'type': 'button','index': 'ex'+node.id},
                          body=True,
                          trigger='hover',
                          ),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              )
            ],
          open=True,
          style={'margin-left': '15px'}
          )
        tree.children.append(
          html.Details(
            [
              html.Summary(
                [
                  html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                  html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                  html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                  html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                  html.P(dcc.Graph(
                    figure=make_data(before, now),
                    config={'displayModeBar': False}
                    ),
                         style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                         )
                  ]
                ),
              html.P('実現手法：' + str(node.other),style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
              ],
            style={'margin-left': '15px', 'marginBottom': '5px'}
            )
          )
      else:
        if node.id == '修正量の低減':
          num = calculate_contribution_percentage(node.id)
          update_save_percent(num, node.id)
          tree = html.Details(
            [
              html.Summary(
                [
                  html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                    'display': 'inline-block','fontSize': 12, 'marginRight': '10px'}),
                  html.P('【下記要求2つで実現】', style={
                    'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                  html.Button(node.id, id='修正量の低減', style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                  dbc.Popover(dbc.RadioItems(options=make_adovaic_node_children_1(node),
                                           id={'type': 'radio','index': node.id}),
                            id='popover',
                          target='修正量の低減',
                          body=True,
                          trigger='hover',
                          ),
                  html.P(com, style={
                    'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                  html.P(dcc.Graph(
                    figure=make_data(before, now),
                    config={'displayModeBar': False},
                    ),
                         style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                         )
                  ]
                )
              ],
            style={'margin-left': '15px'}
            )
        elif node.id == 'テスト自動化':
          for row_3 in df_request[e_request].values:
            if row_3[8] == 3:
              resul = row_3[9].split(',')
              text= row_3[2]
              break
          arc_subchar =[]
          arc_descriptiom =[]
          arc_achivement =[]
          req_subchar =[]
          req_tolerance =[]
          req_achivement =[]
          message =[]
          before_achivement =[]
          for row_4 in df_request[e_request].values:
            for x in resul:
              if row_4[7] == x:
                message +=[row_4[2]]
                no_arc =write_db.check_node(pid,row_4[7])
                arc_subchar +=[no_arc[5]['subchar']]
                arc_descriptiom +=[no_arc[5]['description']]
                arc_achivement +=[no_arc[6]]
                no_req = write_db.check_node(pid,row_4[3])
                req_subchar +=[no_req[5]['subchar']]
                req_tolerance +=[no_req[5]['tolerance']]
                req_achivement +=[no_req[6]]
                before_achivement +=[write_db.check_achievement_old(pid,row_4[7])]
                before_achivement +=[write_db.check_achievement_old(pid,row_4[3])]
          num = calculate_contribution_percentage(node.id)
          update_save_percent(num, text)
          tree = html.Details(
            [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('PQ要求文:', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              ),
            html.Details(
              [
                html.Summary(
                  [
                    html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                    html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                    html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                    html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                    html.P(dcc.Graph(
                      figure=make_data(before, now),
                      config={'displayModeBar': False}
                      ),
                           style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                    ]
                  ),
                html.Details(
                  [
                    html.Summary(
                      [
                        html.P('[50%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                        html.P('PQ要求文：', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                        html.Button(message[0], style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                        html.P('達成:'+str(arc_achivement[0])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                        html.P(dcc.Graph(
                          figure=make_data(before_achivement[0], arc_achivement[0]),
                          config={'displayModeBar': False},
                          ),
                              style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                                  'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                        ]
                      ),
                    html.Details(
                  [
                    html.Summary(
                      [
                        html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                        html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                        html.Button(arc_subchar[0], id={'type': 'button', 'index': arc_subchar[0]}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                        html.P('達成:'+str(arc_achivement[0])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                        html.P(dcc.Graph(
                          figure=make_data(before_achivement[0], arc_achivement[0]),
                          config={'displayModeBar': False}
                          ),
                              style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                              )
                        ]
                      ),
                    html.P('実現手法：' + arc_descriptiom[0],style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'}),
                    html.Details(
                      [
                        html.Summary(
                          [
                            html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                            html.P('品質活動', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                            html.Button(req_subchar[0], id={'type': 'button', 'index': req_subchar[0]}, style={
                                                        'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                            html.P('達成:'+str(req_achivement[0])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                            html.P(dcc.Graph(figure=make_data(before_achivement[1],req_achivement[0] ),config={'displayModeBar': False}),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                        'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                            ]
                          ),
                        html.P('許容範囲：' + str(req_tolerance[0]),
                                            style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
                        ],
                      style={'margin-left': '15px'}
                      )
                    ],
                  style={'margin-left': '15px', 'marginBottom': '5px'}
                  )
              ],
            style={'margin-left': '15px', 'marginBottom': '5px'}
            ),
            html.Details(
              [
                html.Summary(
                  [
                  html.P('[50%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                  html.P('PQ要求文：', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                  html.Button(message[1], style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                  html.P('達成:'+str(arc_achivement[1])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                  html.P(dcc.Graph(
                    figure=make_data(before_achivement[2], arc_achivement[1]),
                    config={'displayModeBar': False},
                    ),
                         style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                            'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                  ]
                ),
                html.Details(
                  [
                    html.Summary(
                      [
                        html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                        html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                        html.Button(arc_subchar[1], id={'type': 'button', 'index': arc_subchar[1]}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                        html.P('達成:'+str(arc_achivement[1])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                        html.P(dcc.Graph(
                          figure=make_data(before_achivement[2], arc_achivement[1]),
                          config={'displayModeBar': False}
                          ),
                              style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                              )
                        ]
                      ),
                    html.P('実現手法：' + arc_descriptiom[1],style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'}),
                    html.Details(
                      [
                        html.Summary(
                          [
                            html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                            html.P('品質活動', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                            html.Button(req_subchar[1], id={'type': 'button', 'index': req_subchar[1]}, style={
                                                        'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                            html.P('達成:'+str(req_achivement[1])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                            html.P(dcc.Graph(figure=make_data(before_achivement[3],req_achivement[1] ),config={'displayModeBar': False}),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                        'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                            ]
                          ),
                        html.P('許容範囲：' + str(req_tolerance[1]),
                                            style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
                        ],
                      style={'margin-left': '15px'}
                      )
                    ],
                  style={'margin-left': '15px', 'marginBottom': '5px'}
                  )
              ],
            style={'margin-left': '15px', 'marginBottom': '5px'}
            ),
            ],
          style={'margin-left': '15px'}
          )
 
                    ],
          open=True,
          style={'margin-left': '15px'}
          )
            
                
    elif node.type == 'ACT':
      if node.parent.type != 'IMP':
        text = ''
        for row in df_request[e_request].values:
          if row[3] == node.id:
            text = row[2]
            break
        num = calculate_contribution_percentage(node.id)
        update_save_percent(num, text)
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('PQ要求文：', style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 10}),
                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline' }),
                dbc.Popover(dbc.RadioItems(options=make_adovaic_node_children(node.id, node),id={'type': 'radio', 'index': node.id}),
                            id='popover',
                            target={'type': 'button','index': 'ex'+node.id},
                            body=True,
                            trigger='hover'
                            ),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                       )
                ]
              )
            ],
          open=True,
          style={'margin-left': '15px'}
          )
        tree.children.append(html.Details(
          [
            html.Summary(
              [
                html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('品質活動', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              ),
            html.P('許容範囲：' + str(node.other),
                               style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
            ],
          style={'margin-left': '15px'}
          )
        )
      else:
        tree= html.Details(
          [
            html.Summary(
              [
                html.P('[100%]', style={
                  'display': 'inline-block', 'fontSize': 12, 'marginRight': '2px', 'marginRight': '10px'}),
                html.P('品質活動', style={
                  'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                  'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                html.P(com, style={
                  'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(
                  figure=make_data(before, now),
                  config={'displayModeBar': False}
                  ),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                       )
                ]
              ),
            html.P('許容範囲：' + str(node.other),
                   style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'}),
            html.P('測定値：' + str(0.40),
                               style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
            ],
          style={'margin-left': '30px'}
          )

    elif node.type == 'QRM':
      tree = html.Details(
        [
          html.Summary(
            [
               html.P('PQ要求文：', style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 10}),
               html.Span(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '15px', 'textDecoration': 'underline', 'fontSize': 12}),
               dbc.Popover(dbc.RadioItems(options=make_adovaic_node(node.id),
                                          id={'type': 'radio', 'index': node.id}
                                          ),
                           id='popover',
                           target={'type': 'button','index': node.id},
                           body=True,
                           trigger='hover',
                           )
              ]
            )
          ],
        open=True,
        style={'margin-left': '15px'}
        )
    if node.children:
      children = [tree_display(child, category,pid,indent + '　')for child in node.children]
      tree.children.append(html.Div(children))

  return tree


'''
●機能：
・編集画面のレイアウト
●id:
・select = 品質モデルの利用者から見えるモデル（品質特性の選択）
・model_free = 品質状態モデルを表示する（編集）
・right_free = データを表示する（実現，活動の情報）
'''


def create_list_from_activities(activities, nodes,current_pid):
    result = []
    global save_percent
    # ノードの辞書を作成して、nidで検索しやすくする
    node_dict = {node.nid: node for node in nodes}
    current_pid = current_pid
    percent_saved = 1
    for activity in activities:
        content = activity.task
        if isinstance(content, dict):
            content = str(content.get('subchar', ''))
        else:
            # contentが辞書でない場合（例えば、floatの場合）を処理
            content = str(content)
        parent_statement = None
        parent_subchar = None
        nid = activity.nid  # アクティビティの nid を取得
        pid = activity.pid
        # 親ノードの情報を取得
        for row in df_request[e_request].values:
          if row[3] == content:
            parent_statement = row[2]
            # parent_subchar = row[1]
            break
        
        if activity.parents:
            parent_nid = activity.parents[0]
            parent_node = node_dict.get(parent_nid)
            
            if parent_node and isinstance(parent_node.task, dict):
                # parent_statement = parent_node.task.get('statement')
                parent_subchar = parent_node.task.get('subchar')
        # if current_pid == str(pid) and isinstance(content, dict) and 'subchar' in content:
        if current_pid == str(pid):
            contribution = None
            for percent, text in save_percent:
                if text == parent_statement:
                    contribution = int(percent)
                    break
                if text == '修正量の低減':
                    percent_saved = percent
            for percent, text in save_percent:
                if text == parent_subchar:
                  if contribution != None:
                    contribution = contribution * percent * 0.01
                    contribution = round(contribution, 1)
                    break
            result.append({
                'nid': nid,
                'name': content,
                'cost': 5,
                'parent': parent_subchar,
                'statement': parent_statement,
                'contribution': contribution  
            })
            # parentでソート
        result = sorted(result, key=lambda x: (x['parent'] is None, x['parent']))
        # '実行時に柔軟性を持たせる' または '複数のクラスで定義できるようにする' の statement を持つエントリの数を数える
        statement_count = sum(1 for item in result if item['statement'] in ['実行時に柔軟性を持たせる', '複数のクラスで定義できるようにする'])
        # result 内の各エントリをチェックして、contribution を設定
        for item in result:
            if item['statement'] in ['実行時に柔軟性を持たせる', '複数のクラスで定義できるようにする']:
                if statement_count > 1:
                    item['contribution'] = int(percent_saved * 0.5)
                    
                else:
                    item['contribution'] = percent_saved
    return result


# 品質活動からachievementが1ではないノードを取得
non_achieved_activities = quality_activity.QualityActivity.get_non_achieved_activities()

# 全てのノードを取得
all_nodes = quality_node.QualityNode.fetch_all_nodes()




# 辞書のリストをカードに変換する関数
def create_list_items(items, members):
    return [
        html.Div(
            dbc.Row(
                [
                    dbc.Col(
                        html.Button(
                            html.Div(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.Div(
                                                f"{item['contribution']}%",  # 数字に%を付ける
                                                style={
                                                    'width': '50px', 'height': '100%', 'border': '1px solid #000',
                                                    'padding': '10px', 'textAlign': 'center', 'backgroundColor': 'lightgray',
                                                    'color': 'black', 'fontWeight': 'bold', 'fontSize': '12px',
                                                }
                                            ),
                                            width=1
                                        ),
                                        dbc.Col(
                                            html.Div(
                                                [
                                                    html.Div(item['parent'], style={'font-size': '18px', 'font-weight': 'bold'}),
                                                    html.Div(item['statement'], style={'font-size': '14px', 'font-weight': 'normal'})
                                                ],
                                                style={'width': '100%', 'height': '100%', 'border': '1px solid #000', 'padding': '10px', 'text-align': 'center', 'background-color': 'blue', 'color': 'white'}
                                            ),
                                            width=4
                                        ),
                                        dbc.Col(
                                            html.Div(item['name'], style={'width': '100%', 'height': '100%', 'border': '1px solid #000', 'padding': '10px', 'text-align': 'center', 'background-color': 'dodgerblue', 'color': 'white', 'font-weight': 'bold'}),
                                            width=4
                                        ),
                                        dbc.Col(
                                            html.Div(f"{item['cost']} MH", style={'width': '70px', 'height': '70px', 'borderRadius': '50%', 'border': '1px solid #000', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center', 'background-color': 'green', 'color': 'white', 'font-weight': 'bold'}),
                                            width=1
                                        )
                                    ],
                                    align='center'
                                ),
                                className="mb-2",
                                style={'width': '100%', 'margin': 'auto'}
                            ),
                            id={'type': 'card', 'nid': item['nid']},
                            style={'border': 'none', 'background': 'none', 'padding': '0', 'width': '100%', 'marginBottom': '10px'}
                        ),
                        width=9  # ボタン部分の幅を設定
                    ),
                    dbc.Col(
                        dcc.Dropdown(
                            id={'type': 'dropdown', 'nid': item['nid']},  # nid を使用
                            options=[{'label': member['mname'], 'value': member['mname']} for member in members],
                            placeholder="Select member",
                            style={'width': '100%', 'display': 'none'},  # 初期状態は非表示
                        ),
                        width=3,  # ドロップダウン部分の幅を設定
                    )
                ],
                align='center',
                className="mb-2",
                style={'width': '100%', 'margin': 'auto'}
            )
        ) for item in items
    ]




assignments = task.TaskAssignment.fetch_all_assignments()
tasks = task.Task.fetch_all_tasks()    
# モーダルウィンドウ内の要素を作成する関数
def create_modal_content(list_ex, members):
    # 新しいメンバー表用の列とデータ
    member_table_columns = [
        {"name": "Name", "id": "mname"},
        {"name": "SprintResource(MH)", "id": "sprint_resource"},
        {"name": "ResourceUsed(MH)", "id": "used_resource"},
        {"name": "残量(MH)", "id": "RemainingResource"}
    ]
    
    member_table_data = [
        {
            "mname": member["mname"],
            "sprint_resource": member["sprint_resource"],
            "used_resource": member["used_resource"],
            "RemainingResource": member['sprint_resource'] - member['used_resource']
        }
        for member in members
    ]
    
    table_columns = [
    {"name": "Name", "id": "mname"},
    {"name": "Tasks", "id": "AssignedTask"}
    ]

    # メンバーの情報に残りのリソースと割り当てタスクの枠（空白）を追加
    table_data = []
    for member in members:
        assigned_tasks = []
        for assignment in assignments:
            if assignment.mid == member["mid"]:
                assigned_task_name = next((task.tname for task in tasks if task.tid == assignment.tid), "")
                if assigned_task_name:
                    assigned_tasks.append(assigned_task_name)
          
        # リストをカンマ区切りの文字列に変換
        assigned_tasks_str = ", ".join(assigned_tasks) if assigned_tasks else ""
        table_data.append({"mname": member["mname"], "AssignedTask": assigned_tasks_str})


    return dbc.Row(
        [   
            dbc.Col(
              dbc.Col(
                dbc.Row([
                  dbc.Col(
                      html.Div(
                          "保守性への貢献度",
                          style={'width': '100%', 'height': '90%', 'border': '1px solid #000', 'padding': '10px', 'text-align': 'center', 'font-weight': 'bold','fontSize':'8px'}
                      ),
                      width=1
                  ),
                  dbc.Col(
                      html.Div(
                          "実現できる品質要求",
                          style={'width': '80%', 'height': '90%', 'border': '1px solid #000', 'margin': '0 0 0 12px','padding': '10px', 'text-align': 'center', 'font-weight': 'bold','fontSize':'13px'}
                      ),
                      width=2
                  ),
                  dbc.Col(
                      html.Div( 
                          "品質活動（タスク）",
                          style={'width': '100%', 'height': '90%', 'border': '1px solid #000', 'padding': '10px', 'text-align': 'center',  'font-weight': 'bold'}
                          ),
                      width=3
                  ),
                  dbc.Col(
                      html.Div( 
                          "コスト",
                          style={'width': '70px', 'height': '70px', 'borderRadius': '50%', 'border': '1px solid #000', 'padding': '10px', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center', 'background-color': 'green', 'color': 'white', 'font-weight': 'bold'}
                          ),
                      width=1
                  ),
                  dbc.Col(
                      html.Div(
                          "作業担当",
                          style={'width': '90%', 'height': '90%', 'border': '1px solid #000', 'margin': '0 12px','padding': '10px', 'text-align': 'center', 'font-weight': 'bold'}
                      ),
                      width=3
                  ),
                ]),
              ),
              width=8
            ),
            dbc.Col(
                html.Div(
                    create_list_items(list_ex, members),
                    style={'max-height': '70vh', 'overflow-y': 'auto'}
                ),
                width=7
            ),
            dbc.Col(
                html.Div(
                    [
                        # dcc.Dropdown(
                        #     id='person-select',
                        #     options=[
                        #         {'label': f'{i} 人', 'value': i} for i in range(1, 100)
                        #     ],
                        #     value=1
                        # ),
                        dash_table.DataTable(
                            id='member-table',
                            columns=member_table_columns,
                            data=member_table_data,
                            style_table={'height': '40%', 'overflowY': 'auto','marginBottom': '0px'},
                            style_cell={'textAlign': 'center'},
                            style_header={'fontWeight': 'bold'},
                        ),
                        html.Div(id='total-person-cost', style={'border': '1px solid #000', 'padding': '10px', 'marginTop': '5px', 'textAlign': 'center', 'font-weight': 'bold'}),
                        html.Div(id='remaining-person-cost', style={'border': '1px solid #000', 'padding': '10px', 'marginTop': '5px', 'textAlign': 'center', 'font-weight': 'bold'}),
                        dash_table.DataTable(
                            id='task-table',
                            columns=table_columns,
                            data=table_data,
                            style_table={'height': '40%', 'overflowY': 'auto', 'marginTop': '5px','marginBottom': '0px'},
                            style_cell={'textAlign': 'center'},
                            style_header={'fontWeight': 'bold'},
                        )
                    ],
                    style={'max-height': '70vh','overflow-y': 'auto'}
                ),
                width=5
            )
        ]
    )
members_data = quality_node.Member.fetch_all_members()
members = [
    {
        "mid": member.mid,
        "pid": member.pid,
        "sprint_resource": member.sprint_resource,
        "used_resource": member.used_resource,
        "mname": member.mname,
        "redmine_id": member.redmine_id
    }
    for member in members_data
] 
for assignment in assignments:
    for member in members:
        if member["mid"] == assignment.mid:
            # タスクのコストを加算
            calc_task = next((t for t in tasks if t.tid == assignment.tid), None)
            if calc_task:
                member["used_resource"] += calc_task.cost

current_pid = ""
list_ex = []
def edit_layout(params):
  global current_pid
  global list_ex
  global members
  current_pid = params.get("pid")
  # 現在のpidと一致するメンバーだけを含める
  members = [
      {
          "mid": member.mid,
          "pid": member.pid,
          "sprint_resource": member.sprint_resource,
          "used_resource": member.used_resource,
          "mname": member.mname,
          "redmine_id": member.redmine_id
      }
      for member in members_data if str(member.pid) == current_pid
  ]  
  # ノードからリストを作成
  list_ex = create_list_from_activities(non_achieved_activities, all_nodes,current_pid)
  return dbc.Container(
   [
      dbc.Row(
        [
          dbc.Col(
            [
              html.Div(
                [
                  dbc.Row(
                    [
                      html.H5('project', style={'flex-direction': 'column', 'backgroundColor': '#2d3748','color': 'white', 'text-align': 'center', 'height': '4vh'}),
                      html.P('project:', style={'display': 'inline-block', 'width': '70px'}),
                      html.P(params.get("project_name", "N/A"), style={'display': 'inline-block', 'width': '200px'}),
                      html.P('sprint:', style={'display': 'inline-block', 'width': '70px'}),
                      html.P(params.get("sprint_num", "N/A"), style={'display': 'inline-block', 'width': '30px'}),
                      html.P(params.get("state", "N/A"), style={'display': 'inline-block', 'width': '100px'}),
                      ]
                    ),
                  dbc.Row(
                    [
                      html.H5('setting', style={'flex-direction': 'column', 'backgroundColor': '#2d3748','color': 'white', 'text-align': 'center', 'height': '4vh'}),
                      ]
                    ),
                  dbc.Row(
                    [
                      dcc.RadioItems(
                        # setting の品質特性選択欄の押下可否は disabled で (福田)
                        options=[
                          {'label': '有効性', 'value': '有効性'},
                          {'label': '効率性', 'value': '効率性', 'disabled': True},
                          {'label': '満足性', 'value': '満足性', 'disabled': True},
                          {'label': 'リスク回避性', 'value': 'リスク回避性', 'disabled': True},
                          {'label': '利用状況網羅性', 'value': '利用状況網羅性', 'disabled': True},
                          {'label': '保守性', 'value': '保守性'},
                          {'label': '移植性', 'value': '移植性', 'disabled': True},
                          ],
                        id='select',
                        labelStyle={'display': 'flex','align-items': 'center','width': '100%','background-color': 'white','marginRight': '20px'}
                        )     
                      ],
                    style={'margin': '0', 'background-color': 'white'}
                    ),
                  dbc.Row([
                    dbc.Col(
                      [
                          dbc.Button(
                              "スプリント計画",
                              id="open-body-scroll",
                              n_clicks=0,
                              style={'width': '100%'}
                          ),
                          dbc.Modal(
                              [
                                  dbc.ModalHeader(
                                      dbc.ModalTitle("計画画面")
                                  ),
                                  dbc.ModalBody(
                                      create_modal_content(list_ex, members), 
                                      id='modal-body-content'
                                  ),
                                  html.Div(id='total-cost', style={'border': '1px solid #000', 'padding': '10px', 'marginTop': '20px', 'textAlign': 'center', 'font-weight': 'bold'}),
                                  dbc.ModalFooter(
                                    [
                                      dbc.Button(
                                            "キャンセル",
                                            id="close-body-scroll",
                                            className="me-2",
                                            n_clicks=0,
                                        ),
                                        dbc.Button(
                                          "確定",
                                          id="confirm-button",
                                          className="ms-2",
                                          n_clicks=0,                                        
                                        )
                                    ],
                                    className="d-flex justify-content-end"
                                  ),
                              ],
                              id="modal-body-scroll",
                              scrollable=False,
                              is_open=False,
                              size="xl",
                               
                          ),
                      ]
                    )
                  ])
                  ]
                )
              ],
            width=2
            ),
          dbc.Col(
            [
              html.Div(
                [
                  dbc.Row(
                    [
                      html.H5('model', style={'flex-direction': 'column', 'backgroundColor': 'black','color': 'white', 'text-align': 'center', 'height': '4vh'}),
                      ]
                    ),
                  dbc.Row(
                    id='model_free',
                    style={'overflow': 'scroll','overflowX': 'scroll','overflowY': 'scroll', 'height': '90vh', 'whiteSpace': 'nowrap', 'overflowWrap': 'normal'}
                    )                  
                  ]
                )
              ], 
            width=3, className='bg-light'),
          dbc.Col(
            [
              html.Div(
                [
                  dbc.Row(
                    [
                      html.H5('Quality condition model',style={'flex-direction': 'column', 'backgroundColor': '#2d3748','color': 'white', 'text-align': 'center', 'height': '4vh'}),
                      ]
                    ),
                  dbc.Row(
                    id='right_free',
                    )
                  ]
                )
              ],
            width=7)
          ],
        style={'height': '95vh'}
        )
      ],
    fluid=True
    )




@callback(
    [Output("modal-body-scroll", "is_open"),
     Output("modal-body-content", "children")],
    [Input("open-body-scroll", "n_clicks"), 
     Input("close-body-scroll", "n_clicks"),
     Input("confirm-button", "n_clicks")],
    [State("modal-body-scroll", "is_open"),
     State({'type': 'card', 'index': ALL}, 'style')]
)
def toggle_modal(open_clicks, close_clicks, confirm_clicks, is_open, card_styles):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "open-body-scroll":
        global list_ex
        global current_pid
        # 品質活動からachievementが1ではないノードを取得
        non_achieved_activities = quality_activity.QualityActivity.get_non_achieved_activities()
        # 全てのノードを取得
        all_nodes = quality_node.QualityNode.fetch_all_nodes()
        list_ex = create_list_from_activities(non_achieved_activities, all_nodes, current_pid)
        return True, create_modal_content(list_ex, members)
    elif button_id == "close-body-scroll":
        return False, dash.no_update
    elif button_id == "confirm-button":
        # 確認ボタンが押されたときの処理
        update_database()
        return False, dash.no_update
    return is_open, dash.no_update

  
def update_database():
    connector = write_db.get_connector()

    try:
        with connector.cursor() as cursor:
            # Taskテーブルの更新
            for task_obj in tasks:
                task_query = """
                INSERT INTO task (tid, tname, nid, cost, parameter)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (tid)
                DO UPDATE SET
                    tname = EXCLUDED.tname,
                    nid = EXCLUDED.nid,
                    cost = EXCLUDED.cost,
                    parameter = EXCLUDED.parameter
                """
                parameter_json = json.dumps(task_obj.parameter)  # 辞書をJSON文字列に変換
                cursor.execute(task_query, (task_obj.tid, task_obj.tname, task_obj.nid, task_obj.cost, parameter_json))

            # Memberテーブルの更新
            for member in members:
                member_query = """
                INSERT INTO member (mid, mname, pid, sprint_resource, used_resource, redmine_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (mid)
                DO UPDATE SET
                    mname = EXCLUDED.mname,
                    pid = EXCLUDED.pid,
                    sprint_resource = EXCLUDED.sprint_resource,
                    used_resource = EXCLUDED.used_resource,
                    redmine_id = EXCLUDED.redmine_id
                """
                cursor.execute(member_query, (member['mid'], member['mname'], member['pid'], member['sprint_resource'], member['used_resource'], member['redmine_id']))

            # TaskAssignmentテーブルの更新
            for assignment in assignments:
                # 既存のレコードを削除するクエリ
                delete_query = """
                DELETE FROM task_assignment WHERE tid = %s
                """
                cursor.execute(delete_query, (assignment.tid,))
                
                # 新しいレコードを挿入するクエリ
                insert_query = """
                INSERT INTO task_assignment (tid, mid)
                VALUES (%s, %s)
                """
                cursor.execute(insert_query, (assignment.tid, assignment.mid))
        # トランザクションをコミット
        connector.commit()

    except Exception as e:
        # エラーが発生した場合はロールバック
        connector.rollback()
        raise e

    finally:
        # コネクションを閉じる
        connector.close()




  
@callback(
    [Output({'type': 'card', 'nid': ALL}, 'style'),
     Output('total-cost', 'children'),
     Output({'type': 'dropdown', 'nid': ALL}, 'style'),
     Output('task-table', 'data'), 
     Output('member-table', 'data'),
     Output('total-person-cost', 'children'),
     Output('remaining-person-cost', 'children')],  
    [Input({'type': 'card', 'nid': ALL}, 'n_clicks'),
     Input({'type': 'dropdown', 'nid': ALL}, 'value')],
    [State({'type': 'card', 'nid': ALL}, 'style'),
     State({'type': 'dropdown', 'nid': ALL}, 'style'),
     State({'type': 'dropdown', 'nid': ALL}, 'id')]
)
def update_selection(n_clicks, selected_values, card_styles, dropdown_styles, dropdown_ids):
    if not n_clicks:
        raise PreventUpdate
    total_cost = 0
    new_card_styles = []
    new_dropdown_styles = []

    # リストの長さを合わせる
    num_items = len(n_clicks)
    if len(card_styles) < num_items:
        card_styles.extend([{} for _ in range(num_items - len(card_styles))])
    if len(dropdown_styles) < num_items:
        dropdown_styles.extend([{} for _ in range(num_items - len(dropdown_styles))])

    for i, clicks in enumerate(n_clicks):
        if clicks and clicks % 2 == 1:
            card_styles[i]['backgroundColor'] = '#d3d3d3'
            dropdown_styles[i]['display'] = 'block'  # プルダウンを表示
            total_cost += list_ex[i]['cost']
        else:
            card_styles[i]['backgroundColor'] = 'white'
            dropdown_styles[i]['display'] = 'none'  # プルダウンを非表示
        new_card_styles.append(card_styles[i])
        new_dropdown_styles.append(dropdown_styles[i])
    
    # プロジェクトIDに基づいてメンバーをフィルタリング
    filtered_members = [
        member for member in members
        if str(member["pid"]) == current_pid
    ]
    
    # タスクの割り当てと同時にメンバーのused_resourceを更新
    for i, value in enumerate(selected_values):
        if value:
            member_mid = next((member['mid'] for member in filtered_members if member['mname'] == value), None)
            if member_mid:
                task_nid = dropdown_ids[i]['nid']
                search_task = next((t for t in tasks if t.nid == task_nid), None)  # tasksからnidが一致するタスクを探す
                if search_task:
                    # 元々の割り当てを削除
                    for assignment in assignments:
                        if assignment.tid == search_task.tid:
                            member = next((member for member in filtered_members if member['mid'] == assignment.mid), None)
                            if member:
                                member['used_resource'] -= search_task.cost
                            assignments.remove(assignment)
                else:
                    # 新しいタスクを作成してtasksに追加
                    if tasks:
                        new_tid = tasks[-1].tid + 1
                    else:
                        new_tid = None
                    new_tname = list_ex[i]['name']  # 対応するカードのnameを取得
                    new_cost = list_ex[i]['cost']   # 対応するカードのcostを取得
                    new_parameter = json.dumps({"example": "value"})  # 必要に応じて適切なパラメータを設定
                    search_task = task.Task(new_tid, new_tname, task_nid, new_cost, new_parameter)
                    tasks.append(search_task)
                new_assignment = task.TaskAssignment(aid=None, tid=search_task.tid, mid=member_mid)
                assignments.append(new_assignment)
                member = next((member for member in filtered_members if member['mid'] == member_mid), None)
                if member:
                    member['used_resource'] += search_task.cost
                
    
    # task-tableのデータ更新
    table_data = []
    for member in filtered_members:
        assigned_tasks = []
        for assignment in assignments:
            if assignment.mid == member["mid"]:
                assigned_task_name = next((task.tname for task in tasks if task.tid == assignment.tid), "")
                if assigned_task_name:
                    assigned_tasks.append(assigned_task_name)
        
        # リストをカンマ区切りの文字列に変換
        assigned_tasks_str = ", ".join(assigned_tasks) if assigned_tasks else ""
        table_data.append({"mname": member["mname"], "AssignedTask": assigned_tasks_str})

    # member-tableのデータ更新
    member_table_data = [
        {
            "mname": member["mname"],
            "sprint_resource": member["sprint_resource"],
            "used_resource": member["used_resource"],
            "RemainingResource": member['sprint_resource'] - member['used_resource']
        }
        for member in filtered_members
    ]
    total_cost2 = 0
    x = 0
    # カードと割り当てられたタスクを比較し、割り当てられたタスクがあればカードのスタイルを変更する
    if n_clicks is not None:
        for i, card in enumerate(new_card_styles):
            card_nid = list_ex[i]['nid']  # カードのnidを取得
            for assignment in assignments:
                assigned_task = next((task for task in tasks if task.tid == assignment.tid), None)
                if assigned_task and assigned_task.nid == card_nid:
                    card['backgroundColor'] = '#d3d3d3'  # カードの背景色を変更
                    total_cost2 += assigned_task.cost
                    # 割り当て済みの人が選択されているプルダウンを表示し、選択された状態にする
                    assigned_member = next((member for member in filtered_members if member['mid'] == assignment.mid), None)
                    if assigned_member:
                        dropdown_id = {'type': 'dropdown', 'nid': card_nid}
                        dropdown_index = dropdown_ids.index(dropdown_id)
                        new_dropdown_styles[dropdown_index]['display'] = 'block'
                        new_dropdown_styles[dropdown_index]['value'] = assigned_member['mname']
                        new_dropdown_styles[dropdown_index]['placeholder'] = assigned_member['mname']
                        
    # 合計コストと残りのコストを計算する
    if x == 0:
      total_cost_mh = total_cost2
      x = 1
    else:
      total_cost_mh = total_cost
    total_sprint_resource = sum(member['sprint_resource'] for member in member_table_data)
    remaining_resource = total_sprint_resource - total_cost_mh

    return new_card_styles, f"Total Cost: {total_cost_mh} MH", new_dropdown_styles, table_data, member_table_data, f"メンバーの総スプリントリソース: {total_sprint_resource} MH", f"使用可能コスト残量: {remaining_resource} MH"



    

@callback(
  Output('model_free', 'children'),
  Output('right_free', 'children'),
  Input('select', 'value'),
  Input({'type': 'button', 'index': ALL}, 'n_clicks'),
  Input({'type': 'radio', 'index': ALL}, 'value'),
  State({'type': 'input', 'index': ALL}, 'value'),
  State({'type': 'dropdown', 'index': ALL}, 'value'),
  State('url', 'href'),
  prevent_initial_call=True
)
def up_node(input_value, button_list, radio_list, input_list, drop_list, url):
  
  if input_value is None:
    return dash.no_update,dash.no_update
  else:
    match = re.search(r'pid=(\d+)', url)
    match1 = re.search(r'category=(\d+)', url)
    if match and match1:
      pid = match.group(1)
      category = match1.group(1)
    #保守性が選ばれたとき
    # drop_list = []
    if (button_list == []) and (radio_list == []) and (input_list == []) and (drop_list == []):
      check_node = write_db.check_node(pid,input_value)
      if check_node == 'none':
        for row in df_square[e_square].values:
          if row[1] == input_value:
            write_db.write_node(pid, row[1], 'REQ', 'qiu', {'subchar': row[1], 'statement': row[2]}, 1, 0, 0)
            break
      node = node_calculation.create_tree(pid, input_value) 
      return tree_display(node,category,pid),dash.no_update
    #トップオーバーが選択されたとき
    elif (input_list == []) and (drop_list == []):
      radio_num = [value for value in radio_list if value is not None]
      button_check = [value for value in button_list if value is not None]      
      if button_check == []:
        for row in df_maintainability[e_maintainability].values:
          if row[1] == radio_num[0]:
            check_node = write_db.check_node(pid,radio_num[0])
            if check_node == 'none':
              write_db.write_node(pid, row[1], 'REQ', 'qiu', {'subchar': row[1], 'statement': row[2]}, search(category, radio_num[0]),write_db.check_node(pid, input_value)[0],0.0) 
            node = node_calculation.make_tree(pid, input_value)
            return tree_display(node,category,pid), dash.no_update
        for row in df_request[e_request].values:
          if row[2] == radio_num[0]:
            if row[8] == 1 or row[8] == 2:
              node1 = node_calculation.make_tree(pid, '保守性')
              node = node_calculation.add_child_to_node(node1, row[1], row[2], 1, 1, 'QRM')
              return tree_display(node,category,pid), dash.no_update
            else:
              result = row[9].split(',')
              for ri in df_request[e_request].values:
                for x in result:
                  if ri[7]==x:
                    check_ar = write_db.check_node(pid, ri[7])
                    check_re = write_db.check_node(pid, ri[3])     
                    if check_ar == 'none' or check_re == 'none':
                      return dash.no_update, ['QP要求文：['+ri[2]+']　'+'の品質実現または，品質活動が未設定のため，追加できません']
              node1 = node_calculation.make_tree(pid, input_value)
              node = node_calculation.add_child_to_node(node1, row[1], radio_num[0], 1, 1, 'QRM')
              return tree_display(node,category,pid), dash.no_update
        return dash.no_update, message_display(radio_num[0],pid)
      else:
        ctx = dash.callback_context
        triggered_id = ctx.triggered_id
        button_id = triggered_id['index']
        for row in df_architecture[e_architecture].values:
          if row[3] == button_id:
            return dash.no_update, message_display(button_id,pid)
        for row in df_request[e_request].values:
          if row[3] == button_id:
            return dash.no_update, message_display(button_id,pid)
        node = node_calculation.make_tree(pid, input_value)
        return tree_display(node,category,pid),dash.no_update
    #更新されたとき
    else:
      radio_num = [value for value in radio_list if value is not None]
      button_check = [value for value in button_list if value is not None]
      if button_check == []:
        return dash.no_update, dash.no_update
      ctx = dash.callback_context
      triggered_id = ctx.triggered_id
      button_id = triggered_id['index']
      if button_id[:3] == 're_':
        index = button_id.index('re_') + len('re_')
        rest_of_text = button_id[index:]
        input_num = [value for value in input_list if value is not None]
        if input_num == []:
          input_num += ['未記入']
        #アーキテクチャの書き込み
        for row1 in df_architecture[e_architecture].values:
          if row1[3] == rest_of_text:
            for row2 in df_request[e_request].values:
              if row2[7] == rest_of_text:
                if row2[8] == 1 :
                  child_node = write_db.check_node(pid,row2[3])
                  if child_node == 'none':
                    write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], write_db.check_node(pid, row1[7])[0],0.0)
                    node = node_calculation.make_tree(pid, input_value)
                    return tree_display(node,category,pid), []
                  else:
                    write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], write_db.check_node(pid, row1[7])[0],0.0,child_node[0])
                    node = node_calculation.make_tree(pid, input_value)
                    return tree_display(node,category,pid), []
                elif row2[8] == 2 :
                  parent_node = write_db.check_node(pid,'修正量の低減')
                  if parent_node == 'none':
                    write_db.write_node(pid, '修正量の低減', 'IMP', 'arch', {'subchar': '修正量の低減', 'description': '以下で実現'}, 1, write_db.check_node(pid, row1[7])[0],0.0)
                    write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], write_db.check_node(pid, '修正量の低減')[0],0.0)
                    node = node_calculation.make_tree(pid, input_value)
                    return tree_display(node,category,pid), []
                  else:
                    child_node = write_db.check_node(pid,row2[3])
                    if child_node == 'none':
                      write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], parent_node[0],0.0)
                      node = node_calculation.make_tree(pid, input_value)
                      return tree_display(node,category,pid), []
                    else:
                      write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], parent_node[0],0.0,child_node[0])
                      node = node_calculation.make_tree(pid, input_value)
                      return tree_display(node,category,pid), []
          else:
            continue
        #品質活動
        for row_1 in df_request[e_request].values:
          if row_1[3] == rest_of_text:
            if row_1[8] == 1:
              parent_node =write_db.check_node(pid,row_1[7])
              if parent_node == 'none':
                write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], write_db.check_node(pid, row_1[1])[0],0.0)
                node = node_calculation.make_tree(pid, input_value)
                return tree_display(node,category,pid), []
              else:
                write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], parent_node[0],0.0)
                node = node_calculation.make_tree(pid, input_value)
                return tree_display(node,category,pid), []
            elif row_1[8]== 2:
              parent_node =write_db.check_node(pid,row_1[7])
              if parent_node == 'none':
                pare_parent_node =write_db.check_node(pid,'修正量の低減')
                if pare_parent_node == 'none':
                  write_db.write_node(pid, '修正量の低減', 'IMP', 'arch', {'subchar': '修正量の低減', 'description': '以下で実現'}, 1, write_db.check_node(pid, row_1[1])[0],0.0)
                  write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], write_db.check_node(pid, '修正量の低減')[0],0.0)
                  node = node_calculation.make_tree(pid, input_value)
                  return tree_display(node,category,pid), []
                else:
                  write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], pare_parent_node[0],0.0)
                  node = node_calculation.make_tree(pid, input_value)
                  return tree_display(node,category,pid), []
              else:
                write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], parent_node[0],0.0)
                node = node_calculation.make_tree(pid, input_value)
                return tree_display(node,category,pid), []
            else:
              write_db.write_node(pid, 'テスト自動化', 'IMP', 'arch', {'subchar': 'テスト自動化', 'description': '以下で実現'}, drop_list[0], write_db.check_node(pid, row_1[1])[0],0.0)
              write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], write_db.check_node(pid, 'テスト自動化')[0],0.0)
              node = node_calculation.make_tree(pid, input_value)
              return tree_display(node,category,pid), []
          else:
            continue
    return dash.no_update,dash.no_update
