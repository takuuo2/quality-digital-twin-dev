import dash
from dash import html, dcc, callback
import dash_bootstrap_components as dbc

dash.register_page(__name__)

def layout(node_id=None, **other_unknown_query_strings):

    import psycopg2

    conn_a = psycopg2.connect(
        host="172.21.40.30", user="postgres", password="selab;", dbname="QDT-DB"
    )
    cursor_a = conn_a.cursor()
    cursor_a.execute(
        "SELECT content ->> 'nft_id' FROM qualitynode where nid = %s", (node_id,)
    )
    catalog_id = cursor_a.fetchone()[0]
    print(catalog_id)

    conn_b = psycopg2.connect(
        host="172.21.40.30", user="postgres", password="selab;", dbname="test_db"
    )
    cursor_b = conn_b.cursor()
    cursor_b.execute(
        "SELECT * FROM catalogs where catalog_id = %s", (catalog_id,)
    )
    test_content = cursor_b.fetchone()
    print(test_content)


    return html.Div(
        children=[
            html.H1(test_content[1]),
            html.Div(
                children=[
                    html.Label('<テスト概要>', style={'fontSize': 15, 'fontWeight': 'bold', 'width': '2'}),
                    html.P(test_content[2], style={'width': '5'})
                ],
                #style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'width': '20%'}
            ),
            html.Div(
                children=[
                    html.Label('<関連する品質特性>', style={'fontSize': 15, 'fontWeight': 'bold', 'width': '2'}),
                    html.P(test_content[3], style={'width': '5'})
                ],
                #style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'width': '20%'}
            ),
        ]
    )