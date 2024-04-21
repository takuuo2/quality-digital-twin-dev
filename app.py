import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output
from urllib.parse import urlparse, parse_qs
from urllib import parse
from pages import home, edit, create_category, db, dashboard
from nft import nft

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


'''
●機能
・システム全体のレイアウト
●id
・url = URL
・page-content = ここに処理をしている
'''

app.layout = html.Div(
  [
    dcc.Location(
      id='url',
      refresh=False
      ),
    dbc.NavbarSimple(
      children = [dbc.NavItem(dbc.NavLink('save/back', href='/home'))],
      brand='Quality Digital Twin',
      color='dark',
      dark=True,
      style={'height': '30px'},
      brand_style={'position': 'absolute',
                   'left': '0',
                   'margin-left': '15px'}
      ),
    html.Div(id='page-content')
    ]
  )


#実行ファイルを移す
@app.callback(
  Output('page-content', 'children'),
  Input('url', 'href')
  )
def display_page(href):
  print('href : %s' %href)
  url_components = parse.urlparse(href)
  pathname = url_components.path
  print('pathname : %s' %pathname)
  if pathname == '/':
    return home.home_layout()
  else:
    params = {k: v[0] if len(v) == 1 else v for k, v in dict(parse.parse_qs(url_components.query)).items()}
    pathname_part = pathname.split('?')[0]
    parsed_url = urlparse(pathname)
    query_params = parse_qs(parsed_url.query)
    project_name = query_params.get('project_name', [None])[0]
    category_num = query_params.get('category', [None])[0]
    sprint_num = query_params.get('sprint_num', [None])[0]
    state = query_params.get('state', [None])[0]
    pid = query_params.get('pid', [None])[0]
    nid = query_params.get('nid', [None])[0]
    
    if pathname_part == '/home':
      return home.home_layout(project_name, category_num)
    elif pathname == '/create_category': 
      return create_category.create_category_layout()      
    elif pathname_part =='/edit':
      return edit.edit_layout(params)
    elif pathname_part =='/db':
      return db.db_layout(params)
    elif pathname_part =='/dashboard':
      return dashboard.dashboard_layout(params)
    elif pathname_part =='/nft':
      return nft.nft_layout(params)

if __name__ == '__main__':
    app.run_server(debug=True)
