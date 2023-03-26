import dash
import dash_leaflet as dl
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash import dash_table
import dash_bootstrap_components as dbc
from src.sql_query import query_items, get_cities, get_stores, get_items_in_store
import base64
import dash_auth

# Login
VALID_USERNAME_PASSWORD_PAIRS = [['naya', 'naya']]
app = dash.Dash(__name__, title='Prices App', external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

logo_png = 'compare.png'
logo_base64 = base64.b64encode(open(logo_png, 'rb').read()).decode('ascii')

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([html.Img(src='data:image/png;base64,{}'.format(logo_base64), style={'height': '50%',
                                                                                     'width': '50%',
                                                                                     'margin-top': 20})], width=3),
        dbc.Col(
            html.H1("Shopping basket comparison",
                    style={"text-align": "center", "font-family": "roboto", "font-weight": "bold"}),
            style={'margin-top': 20},
            width=6
        ),
        dbc.Col(width=3)
    ]),

    dbc.Row([
        dbc.Col(
            html.Div([
                html.Label("1. Choose a city:", style={"font-weight": "bold"}),
                dcc.Dropdown(id="city_dropdown", options=get_cities(),
                             placeholder="Select a city...", value='ירושלים',
                             style={"height": "40px"}),
            ]),
            width=3,
        ),
        dbc.Col(width=1),
        dbc.Col(
            html.Div([
                html.Label("2. Choose a store:", style={"font-weight": "bold"}),
                dcc.Dropdown(id="store_dropdown", placeholder="Select a store...",
                             style={"height": "40px"}),
            ]),
            width=3,
        ),
        dbc.Col(width=1),
        dbc.Col(
            html.Div([
                html.Label("3. Choose items:", style={"font-weight": "bold"}),
                dcc.Dropdown(id="item_dropdown", placeholder="Select an item...", multi=True,
                             style={"height": "40px"}),
            ]),
            width=3,
        )
    ], style={"margin-bottom": "20px", "margin-top": "10px"}),

    dbc.Row([
        dbc.Col(
            html.Button("Search", id="search_button", disabled=False),
            style={"text-align": "center", 'font-family': 'roboto'},
            width=12,
        )
    ], style={"margin-bottom": "20px"}),
    dbc.Row([
        dbc.Col(
            dcc.Loading(
                id="loading",
                children=[dash_table.DataTable(id="results_table",
                                               columns=[{"name": "City", "id": "city"},
                                                        {"name": "Store Name", "id": "storename"},
                                                        {"name": "Store Address", "id": "address"},
                                                        {"name": "Total Price (ILS)", "id": "total_price"}],
                                               data=[],
                                               style_table={'overflowX': 'auto'},
                                               style_header={
                                                   'backgroundColor': 'rgb(230, 230, 230)',
                                                   'fontWeight': 'bold',
                                                   'textAlign': 'center'
                                               },
                                               style_cell={
                                                   'font-family': 'roboto',
                                                   'textAlign': 'center',
                                                   'padding': '10px',
                                                   'whiteSpace': 'normal',
                                                   'height': 'auto'
                                               },
                                               style_data_conditional=[
                                                   {
                                                       'if': {'row_index': 'odd'},
                                                       'backgroundColor': 'rgb(248, 248, 248)'
                                                   }
                                               ],
                                               ),
                          ],
                type="default",
            ),
            width=12,
        )
    ], style={"margin-bottom": "20px"}),
    dbc.Row([
        dbc.Col(
            dl.Map(id="store_map", zoom=12, children=[dl.TileLayer()], center=[31.771959, 35.217018],
                   style={'width': '100%', 'height': '50vh'}),
            width=12,
        )
    ])
], fluid=True)


# Add callback to update stores based on the selected city
@app.callback(
    Output("store_dropdown", "options"),
    [Input("city_dropdown", "value")]
)
def update_stores(selected_city):
    if selected_city is None:
        return []
    return get_stores(selected_city)


# Add callback to update items based on the selected store
@app.callback(
    Output("item_dropdown", "options"),
    [Input("store_dropdown", "value")]
)
def update_items(selected_store):
    if selected_store is None:
        return []
    return get_items_in_store(selected_store)


# Update the existing callback to include selected_store
@app.callback(
    [Output("results_table", "data"),
     Output("store_map", "children"),
     Output("store_map", "center"),
     Output("store_map", "zoom")],
    [Input("search_button", "n_clicks")],
    [State("item_dropdown", "value"),
     State("city_dropdown", "value"),
     State("store_dropdown", "value")]
)
def update_table_and_map(n_clicks, selected_item, selected_city, selected_store):
    if n_clicks is None or selected_item is None or selected_city is None or selected_store is None:
        return [], [dl.TileLayer()], [31.771959, 35.217018], 12

    df = query_items(selected_item, selected_city)

    result_data = df.to_dict("records")

    store_locations = df[["latitude", "longitude", "storename"]].drop_duplicates()

    markers = [
        dl.Marker(position=[lat, lon], children=[dl.Tooltip(storename)])
        for lat, lon, storename in store_locations.itertuples(index=False, name=None)
    ]

    # Calculate the average latitude and longitude
    avg_latitude = store_locations["latitude"].mean()
    avg_longitude = store_locations["longitude"].mean()

    # Update the map with the new center and zoom level
    return result_data, [dl.TileLayer(), *markers], [avg_latitude, avg_longitude], 10


if __name__ == "__main__":
    app.run_server(debug=True)
