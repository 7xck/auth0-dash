from dash import Dash, html, dcc
import dash
import plotly.express as px
import pandas as pd

df = pd.DataFrame(
    {
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"],
    }
)

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")


def layout():
    return html.Div(
        children=[
            html.H1(children="Hello Dash"),
            html.Div(
                children="""
        Dash: A web application framework for your data.
    """
            ),
            dcc.Graph(id="example-graph", figure=fig),
        ]
    )


dash.register_page(__name__, path="/other_page")
