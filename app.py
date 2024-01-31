import os
from sys import platform

import dash
import dash_bootstrap_components as dbc
import sass
from dash import Input, Output, State, callback

from auth.auth0 import Auth0Auth

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    use_pages=True,
    # assets_folder="assets",
)

auth = Auth0Auth(app)

if __name__ == "__main__":
    app.run_server(debug=True, port=3000)
