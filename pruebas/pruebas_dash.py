import dash
from dash import html, dcc, Input, Output, State
import plotly.express as px
import pandas as pd
from pymongo import MongoClient

# Conexión a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client["youtube_sponsors"]
coleccion = db["sponsored_videos"]

# App Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard de Patrocinadores"),

    html.Div([
        html.H2("Patrocinadores más frecuentes"),
        dcc.Graph(id="grafico-patrocinadores"),
    ]),

    html.Div([
        html.H2("Buscar patrocinadores por canal o viceversa"),
        dcc.Input(id="input-busqueda", type="text", placeholder="Escribe patrocinador o canal"),
        dcc.Dropdown(
            id='dropdown-tipo',
            options=[
                {'label': 'Patrocinador ➡️ Canales', 'value': 'patrocinador'},
                {'label': 'Canal ➡️ Patrocinadores', 'value': 'canal'}
            ],
            value='patrocinador'
        ),
        html.Button('Buscar', id='boton-buscar', n_clicks=0),
    ]),

    dcc.Graph(id="grafico-principal"),
])

# Callback para gráficos
@app.callback(
    Output('grafico-principal', 'figure'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
    Input('dropdown-tipo', 'value'),
)
def actualizar_grafico(tipo_busqueda, texto_busqueda):
    if tipo_busqueda == "patrocinador":
        pipeline = [
            {"$match": {"sponsors.brand_name": texto_busqueda}},
            {"$group": {"_id": "$channel_name", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}}
        ]
        titulo = f"Canales patrocinados por {texto_busqueda}"
        eje_x = "_id"

    else:
        pipeline = [
            {"$match": {"channel_name": texto_busqueda}},
            {"$unwind": "$sponsors"},
            {"$group": {"_id": "$sponsors.brand_name", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}}
        ]
        eje_x = "_id"
        texto_busqueda = texto_busqueda

    datos = list(coleccion.aggregate(pipeline))

    if tipo_busqueda == "patrocinador":
        df = pd.DataFrame(datos, columns=["canal", "total"])
        fig = px.bar(df, x="canal", y="total", title=f"Canales patrocinados por {texto_busqueda}")

    else:
        df = pd.DataFrame(datos, columns=["patrocinador", "total"])
        fig = px.bar(df, x="patrocinador", y="total", title=f"Patrocinadores del canal {texto_busqueda}")

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
