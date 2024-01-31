from dash import Dash, html, dcc
import dash
import plotly.express as px
import pandas as pd
import flask

df = pd.DataFrame(
    {
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"],
    }
)

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")


def layout():
    name = flask.request.cookies.get("AUTH-USER")
    return html.Div(
        children=[
            html.H1(children=f"Authorisation with auth0! Hello {name}"),
            html.Div(
                children="""
        This is just a little test dash to show off auth!
    """
            ),
            dcc.Graph(id="example-graph", figure=fig),
            html.A(
                "Logout",
                id="logout-button",
                href="/logout",
                style={
                    "textAlign": "center",
                    "display": "inline-block",
                    "margin": "10px",
                    "padding": "10px",
                    "background-color": "#007bff",
                    "color": "white",
                    "text-decoration": "none",
                    "border-radius": "5px",
                },
            ),
        ]
    )


dash.register_page(__name__, path="/")
