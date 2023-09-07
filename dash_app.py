import base64
import io
import sqlite3
import time
from secrets import token_urlsafe
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

submit_modal = dbc.Modal(
    [
        dbc.ModalHeader([html.H5("Load Data")]),
        dbc.ModalBody([

            dbc.InputGroup([dbc.InputGroupText('n_obs'),
                            dbc.Input(placeholder='n_obs', type='number', id='n_obs', min=1)]),

            html.Hr(),
            dbc.Row(
                dcc.Upload('Drag and Drop or click',
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
                           id='upload-file')
            ),
            dbc.Row(
                # Hidden alert in case wrong file format gets loaded
                dbc.Alert(
                    "ERROR. Supported file formats: .tsv or .csv",
                    id="alert-file-fmt",
                    dismissable=True,
                    fade=True,
                    is_open=False,
                    duration=5000,
                    color="danger"
                )
            )
        ]),

        dbc.ModalFooter([
            dbc.Button("Submit", color="primary", href="https://t.me/koshmarkersbot", id="tg-link-button", active=False),
            dbc.Button("Close", color="secondary", id="submit-close", className="submit-bn")
        ]),
    ],
    id="submit-modal",
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
    "Load Demo",
    id="demo-button",
    outline=True,
    color="primary",
    style={"textTransform": "none", "white-space": "nowrap"},
)

button_submit = dbc.Button(
    "Upload File",
    id="submit-button",
    outline=True,
    color="primary",
    style={"textTransform": "none", "font-weight": "bold", "white-space": "nowrap"},
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
                                        dbc.NavItem(button_submit, style={'padding': '1rem', "font-weight": "bold"}),
                                        # todo add |
                                        dbc.NavItem(button_demo, style={'padding': '1rem', "textTransform": "none"}),
                                        dbc.NavItem(button_howto, style={'padding': '1rem', "textTransform": "none"}),
                                        # Todo add result history
                                    ],
                                    navbar=True,
                                ),
                                id="navbar-collapse",
                                navbar=True,
                            ),
                            modal_overlay,
                            submit_modal,
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

data_table = dash_table.DataTable(
    id='data-table',
    columns=[
        dict(id='Gene', name='Gene'),
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


def get_heatmap(hm) -> go.Figure:
    """
    Create heatmap from passed DataFrame
    :param pd.DataFrame hm:
    :return:
    """

    # Y-axis legend
    y_ticks = pd.Series(data="", index=hm.index, dtype=str)
    prev_stack_len = 0  # for correct tick positioning
    for i in hm.condition.unique():
        cond_len = hm.loc[hm.condition == i].shape[0]  # length of condition
        cond_pos = prev_stack_len + cond_len // 2

        # Y-axis text position
        y_ticks.loc[cond_pos] = str(i)

        if hm.loc[0, 'condition'] == i:  # No borderline for first group (edge of heatmap)
            prev_stack_len += cond_len
            continue

        # insert a row after cond_one_pos to make it visible
        line = pd.DataFrame(data=hm.max().max(), columns=hm.columns, index=[0])
        hm = pd.concat([hm.loc[:prev_stack_len - 1], line, hm.loc[prev_stack_len:]]).reset_index(drop=True)

        prev_stack_len += cond_len + 1
        y_ticks.loc[y_ticks.shape[0]] = ""  # add empty line to fit hm.shape
    hm = hm.drop(columns='condition')

    fig = go.Figure()
    # fig.add_trace(go.Heatmap(z=np.log10(hm).fillna(0), x=hm.columns)).update_layout(margin={'l': 0, 'r': 0, 't': 0, 'b': 0})
    fig.add_trace(go.Heatmap(z=hm, x=hm.columns)).update_layout(margin={'l': 0, 'r': 0, 't': 0, 'b': 0})

    fig.update_yaxes(tickmode='array',
                     tickvals=np.arange(0, hm.shape[0]),
                     ticktext=y_ticks)  # todo hovertext
    return fig


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
    table = pd.read_csv('./data/demo_results_stat.txt', sep='\t')  # Важно!!! columns == ids в data_table
    table = table.to_dict('records')

    # Heatmap
    hm = pd.read_csv('./data/demo_results_hm.txt', sep='\t')
    hm = hm[hm.columns[::-1]]
    fig = get_heatmap(hm)

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


def create_link_to_telegram():
    """
    Generate link for automatic Telegram bot auth (with start action) and token for assigning a job token.
    :return: link, token
    """

    token = str(token_urlsafe(16))
    token = f'{token}_{time.time_ns()}'
    tg_link = f"https://telegram.me/koshmarkersbot?start={token}"
    return tg_link, token


# TODO Scedule calculations on file input
@app.callback(
    Output("alert-file-fmt", "is_open"),
    Output('upload-file', 'disabled'),
    Output('tg-link-button', 'disabled'),
    Output('tg-link-button', 'href'),
    Input('upload-file', 'contents'),  # todo trigger on final send button
    State('upload-file', 'filename'),
    State('n_obs', 'value'),
    prevent_initial_call=True
)
def load_file(contents, filename, n_obs):
    if not contents:
        raise PreventUpdate
    else:
        df = parse_contents(contents, filename)
        if isinstance(df, str):
            return True, False, True, "https://t.me/koshmarkersbot"  # Raise alert if failed to parse file

    # checks were passed in load_file
    df = parse_contents(contents, filename)

    # Create link and token for a job, load into db for further auth in Telegram
    tg_link, job_token = create_link_to_telegram()

    # Write file with token as name, filename is kept only for notifications
    df.to_csv(f"./data/{job_token}.csv", sep='\t', index=False)

    with sqlite3.connect("tg/jobs.db") as con:
        cur = con.cursor()
        cur.execute("INSERT INTO jobs (filename, job_token, n_obs) VALUES (?, ?, ?)", (filename, job_token, int(n_obs)))
        con.commit()
    con.close()

    return False, True, False, f"https://t.me/koshmarkersbot?start={job_token}"  # Open a button with a link to tg


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

    # table_df = table_df.to_dict('records')
    # fig = get_heatmap(hm)
    return None


# Table row info on data_table click
@app.callback(
    Output('data-table-row-info', 'children'),
    Input('data-table', 'active_cell')
)
def table_row_info(active_cell):
    # todo get row content, return useful data
    return str(active_cell) if active_cell else "Click on a row to view additional info"


# Table row info on data_table click
@app.callback(
    Output("heatmap_graph", "figure", allow_duplicate=True),
    Input('data-table', "derived_virtual_data"),
    Input('data-table', "derived_virtual_selected_rows"),
    Input('update-heatmap', "n_clicks"),
    State("hm_fn", "children"),
    prevent_initial_call=True
)
def update_heatmap(rows, derived_virtual_selected_rows, hm_fn, n_clicks):
    # When the table is first rendered, `derived_virtual_data` and
    # `derived_virtual_selected_rows` will be `None`. This is due to an
    # idiosyncrasy in Dash (unsupplied properties are always None and Dash
    # calls the dependent callbacks when the component is first rendered).
    # So, if `rows` is `None`, then the component was just rendered
    # and its value will be the same as the component's dataframe.
    # Instead of setting `None` in here, you could also set
    # `derived_virtual_data=df.to_rows('dict')` when you initialize
    # the component.

    if not hm_fn or not n_clicks:  # file not loaded
        raise PreventUpdate

    # Load file
    hm = pd.read_csv(hm_fn, sep='\t')

    # Filter data

    # Get figure
    fig = get_heatmap(hm)

    return fig


# Callback for Info popup button
@app.callback(
    Output("modal", "is_open"),
    [Input("howto-open", "n_clicks"), Input("howto-close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_info(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Callback for Submit popup button
@app.callback(
    Output("submit-modal", "is_open"),
    [Input("submit-button", "n_clicks"), Input("submit-close", "n_clicks")],
    [State("submit-modal", "is_open")],
)
def toggle_submit(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Compile layout
app.layout = html.Div(
    [
        # content will be rendered in this element
        html.Div(id='content'),

        header,
        html.Br(),
        dbc.Container(
            [
                dbc.Row(
                    id="header-content",
                    children=[dbc.Col(upload_info, md=6), dbc.Col(heatmap_info, md=6)],
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

        # Invisible elements for client-side variable storage (yeah)

        # represents the URL bar, doesn't render anything
        dcc.Location(id='url', refresh=False),

        # trigger for page_loaded bool - to distinguish between reset filters and page initial load
        html.Div(id='page_loaded', children=0, style=dict(display='none')),

        # filename variables - to update graphs from files
        html.Div(id='stat_fn', children="", style=dict(display='none')),
        html.Div(id='hm_fn', children="", style=dict(display='none')),

    ]
)


def open_browser():
    webbrowser.open_new("http://localhost:8070")


if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(debug=True, port=8070)
