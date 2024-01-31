from dash import dcc, html
import dash_bootstrap_components as dbc
import dash

content = html.Div(
    id="page-content",
    className="ml-64 mr-2 py-8 px-4 transition-all duration-300 ease-in-out",
    children=[
        html.Div(
            [
                html.Div(
                    dcc.Link(
                        f"{page['name']} - {page['path']}",
                        href=page["relative_path"],
                    )
                )
                for page in dash.page_registry.values()
            ]
        ),
        dash.page_container,
    ],
)

make_navlink = lambda name, href: dbc.NavLink(
    name, href=href, active="exact", className="text-white hover:text-epochPurpleLight"
)

layout = html.Div(
    id="app",
    children=[
        dcc.Location(id="url"),
        # toggle_sidebar,
        # sidebar,
        content,
    ],
)
