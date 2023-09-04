import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import webbrowser
from threading import Timer


external_stylesheets = [dbc.themes.BOOTSTRAP, "assets/segmentation-style.css"]
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server
app.title = 'BioKoshmarkers'

# Howto
with open("assets/howto.md", "r", encoding='utf-8') as f:
    howto_md = f.read()


modal_overlay = dbc.Modal(
    [
        dbc.ModalBody(html.Div([dcc.Markdown(howto_md)], id="howto-md")),
        dbc.ModalFooter(dbc.Button("Закрыть", id="howto-close", className="howto-bn")),
    ],
    id="modal",
    size="lg",
)

button_howto = dbc.Button(
    "Инфо",
    id="howto-open",
    outline=True,
    color="info",
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
                    dbc.Col(dbc.NavbarBrand("Здесь могло быть название", className="ms-2")),
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
                                        dbc.NavItem(button_howto),
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


app.layout = html.Div(
    [
        header,
        # dbc.Container(
        #     [
        #         dbc.Row(
        #             id="app-content",
        #             children=[dbc.Col(sidebar)]  #, dbc.Col(diagram, md=8)],
        #         ),
        #     ],
        #     fluid=True,
        # ),
    ]
)


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


def open_browser():
    webbrowser.open_new("http://localhost:8070")


if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=True, port=8070)

