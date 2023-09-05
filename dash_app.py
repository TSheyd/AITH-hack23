import base64
import io
import time
from threading import Timer

import webbrowser
from furl import furl

import pandas as pd
import numpy as np

from dash import Dash, dcc, html, dash_table, Input, Output, State, ctx
from dash.dash_table.Format import Format, Scheme
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from Main import MarkerFinder


external_stylesheets = [dbc.themes.BOOTSTRAP, "assets/segmentation-style.css"]
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server
app.title = 'BioKoshmarkers'

# App Layout

# Howto button
with open("assets/howto.md", "r", encoding='utf-8') as f:
    howto_md = f.read()

modal_overlay = dbc.Modal(
    [
        dbc.ModalBody(html.Div([dcc.Markdown(howto_md)], id="howto-md")),
        dbc.ModalFooter(dbc.Button("Close", id="howto-close", className="howto-bn")),
    ],
    id="modal",
    size="lg",
)

button_howto = dbc.Button(
    "Info",
    id="howto-open",
    outline=True,
    color="info",
    # Turn off lowercase transformation for class .button in stylesheet
    style={"textTransform": "none"},
)

button_demo = dbc.Button(
    "Demo",
    id="demo-button",
    outline=True,
    color="primary",
    # Turn off lowercase transformation for class .button in stylesheet
    style={"textTransform": "none"},
)

# Header
header = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    # Логотипчика пока нет
                    # dbc.Col(
                    #     html.Img(
                    #         id="logo",
                    #         src=app.get_asset_url("./.png"),
                    #         height="30px",
                    #     ),
                    #     md="auto",
                    # ),
                    dbc.Col(dbc.NavbarBrand("ML-Based Biomarker Discovery on Bulk RNA-Seq Data", className="ms-2")),
                ],
                align="center",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.NavbarToggler(id="navbar-toggler"),
                            dbc.Collapse(
                                dbc.Nav(
                                    [
                                        dbc.NavItem(button_demo, style={'padding': '1rem'}),
                                        dbc.NavItem(button_howto, style={'padding': '1rem'}),
                                    ],
                                    navbar=True,
                                ),
                                id="navbar-collapse",
                                navbar=True,
                            ),
                            modal_overlay,
                        ],
                        md=2,
                    ),
                ],
                align="center",
            ),
        ],
        fluid=True,
    ),
    dark=True,
    color="dark",
    sticky="top",
)

# Info header - upload info and graph info
upload_info = html.Div(
    [
        html.H5("Upload info"),
        html.Hr(),
        dcc.Markdown("Some text"),
    ],
    id="upload-info",
    className="pretty_container",
)

heatmap_info = html.Div(
    [
        html.H5("Graph info"),
        html.Hr(),
        dcc.Markdown("Some text"),
    ],
    id="heatmap-info",
    className="pretty_container",
)

# Upload button
upload_ = (
    dbc.Card(
        id="upload-card",
        children=[
            dbc.CardBody(
                [
                    html.Div([
                        dcc.Upload('Drag and Drop or select a File',
                                   style={
                                       'width': '100%',
                                       'height': '60px',
                                       'lineHeight': '60px',
                                       'borderWidth': '1px',
                                       'borderStyle': 'dashed',
                                       'borderRadius': '5px',
                                       'textAlign': 'center',
                                       'cursor': 'pointer'
                                   },
                                   multiple=False,  # Allow multiple files to be uploaded
                                   id='upload-file'),
                        html.Div(id='output-data-upload'),

                        # Hidden alert in case wrong file format gets loaded
                        dbc.Alert(
                            "ERROR. Supported file formats: .tsv or .csv",
                            id="alert-file-fmt",
                            dismissable=True,
                            fade=True,
                            is_open=False,
                            duration=5000,
                            color="danger"
                        ),
                    ])
                ]
            ),
        ],
    ),
)


data_table = dash_table.DataTable(
    id='data-table',
    columns=[
        dict(id='Feature', name='Feature'),
        dict(id='Groups', name='Group'),
        dict(id='pval', name='p-value', type='numeric', format=Format(precision=2, scheme=Scheme.exponent)),
        dict(id='padj', name='p-value (adj)', type='numeric', format=Format(precision=2, scheme=Scheme.exponent))
    ],
    data=[{}],  # Input
    editable=False,
    filter_action="native",
    sort_action="native",
    sort_mode="multi",
    column_selectable="single",
    selected_columns=[],
    selected_rows=[],
    page_action="native",
    page_current=0,
    page_size=10,
    style_cell={
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'minWidth': '100px', 'width': '120px', 'maxWidth': '120px',
        'padding': '5px',
    },
    style_table={'overflowY': 'auto'},
    style_header={
        'backgroundColor': 'white',
        'fontWeight': 'bold',
        'fontsize': 8,
        'font-family': 'sans-serif'
    },
    style_data={'fontsize': 6, 'font-family': 'sans-serif'},
)

# Wrap table in a loading animation,
data_table = [
    html.Div(
        id="table-loader-wrapper",
        style={"height": "100%"},
        children=[dcc.Loading(
            id="table-loading",
            parent_style={"height": "100%"},
            type="circle",
            children=[data_table])]
    ),
    html.Div(dbc.Alert("", color="light", id='data-table-row-info'))
]


# TODO Diagram
heatmap_graph = dcc.Graph(id='heatmap_graph', className="m-0")

# Wrap diagram in a loading animation
heatmap_graph = html.Div(
    id="heatmap-loader-wrapper",
    style={"height": "100%"},
    children=[dcc.Loading(
        id="heatmap-loading",
        parent_style={"height": "100%"},
        type="circle",
        children=[heatmap_graph])
    ])


# Func to load diagram from table
def get_heatmap(df):
    df = pd.DataFrame(np.random.rand(100, 100))

    fig = go.Figure(data=go.Heatmap(
        z=df,
        colorscale='Viridis'))

    fig.update_layout(
        autosize=False,
        width=500,
        height=500,
        margin=dict(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ),
    )

    return fig


# Callback для окна "инфо"
@app.callback(
    Output("modal", "is_open"),
    [Input("howto-open", "n_clicks"), Input("howto-close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_info(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Demo results
@app.callback(
    Output('data-table', 'data', allow_duplicate=True),
    Output("heatmap_graph", "figure", allow_duplicate=True),
    Input('demo-button', 'n_clicks'),
    prevent_initial_call=True  # todo возможно апп можно загружать уже с демо-данными?
)
def demo(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    # Table
    table = pd.read_csv('./data/results.txt', sep='\t')  # Важно!!! columns == ids в data_table
    table = table.to_dict('records')

    # Heatmap
    heatmap_df = pd.DataFrame(np.random.rand(100, 100))  # heatmap пока на рандоме
    fig = go.Figure()
    fig.add_trace(go.Heatmap(z=heatmap_df)).update_layout(margin={'l': 0, 'r': 0, 't': 0, 'b': 0})
    return table, fig


def parse_contents(contents, filename):
    """
    Read raw input data
    """
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if '.csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif '.txt' in filename:
            # Assume that the user uploaded an Excel file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep='\t')
        elif '.xls' in filename:
            # Assume that the user uploaded an Excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return f'File format not supported. Recommended file formats: tsv or csv'
    except Exception as e:
        return f'There was an error processing this file: {e}'
    return df


# Launch async calculations on file input
@app.callback(
    Output("alert-file-fmt", "is_open"),
    Input('upload-file', 'contents'),
    State('upload-file', 'filename'),
    prevent_initial_call=True
)
def start_calculations(contents, filename):
    if not contents:
        raise PreventUpdate
    else:
        df = parse_contents(contents, filename)
        if isinstance(df, str):
            return True

    MarkerFinder(df, "condition", 50, 50, f"./data/{filename}results.txt")

    # todo log start of calc and setup tg notifications

    return False


# Parse URL with token to retrieve calculated data
@app.callback(
    Output('data-table', 'data', allow_duplicate=True),
    Output("heatmap_graph", "figure", allow_duplicate=True),
    Input('url', 'href'),
    prevent_initial_call='initial_duplicate'
)
def _content(href: str):
    # User authentication
    try:
        url = furl(href)
        token = url.args["token"]
    except KeyError:  # no token provided
        raise PreventUpdate

    # format loaded file
    # table_df = table_df.to_dict('records')
    # fig = go.Figure()
    # fig.add_trace(go.Heatmap(z=heatmap_df)).update_layout(margin={'l': 0, 'r': 0, 't': 0, 'b': 0})
    return None


# Table row info on data_table click
@app.callback(
    Output('data-table-row-info', 'children'),
    Input('data-table', 'active_cell')
)
def table_row_info(active_cell):
    # todo get row content, return useful data
    return str(active_cell) if active_cell else "Click on a row to view additional info"


# Compile layout
app.layout = html.Div(
    [
        # represents the URL bar, doesn't render anything
        dcc.Location(id='url', refresh=False),

        # content will be rendered in this element
        html.Div(id='content'),

        header,
        html.Br(),
        dbc.Container(
            [
                dbc.Row(
                    id="header-content",
                    children=[dbc.Col(upload_info, md=4), dbc.Col(upload_, md=2), dbc.Col(heatmap_info, md=6)],
                ),
                html.Br(),
                dbc.Row(
                    id="app-content",
                    children=[dbc.Col(data_table, md=6), dbc.Col(heatmap_graph, md=6)],
                ),
                html.Br(),
                dbc.Row(
                    id="footer-content",
                    children=[],  # todo: some sort of further calculations with acquired data
                ),
            ],
            fluid=True,
            style={"height": "100vh"}
        ),
    ]
)


def open_browser():
    webbrowser.open_new("http://localhost:8070")


if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(debug=True, port=8070)
