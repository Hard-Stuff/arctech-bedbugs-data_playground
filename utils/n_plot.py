import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html
import os


def load_and_prepare_data(folder, filenames):
    data_list = []
    for file in filenames:
        full_path = os.path.join(folder, file + ".csv")
        df = pd.read_csv(full_path)
        df["relative_time"] = (
            df["timestamp"] - df["timestamp"].iloc[0]
        ) / 1000  # ms → s
        data_list.append(df)
    return data_list


def create_dash_app(
    folder, filenames, titles=None, master_title="Sensor Comparison Dashboard"
):

    if titles is None:
        titles = filenames

    data_list = load_and_prepare_data(folder, filenames)

    # Build multi-subplot figure
    fig = make_subplots(
        rows=len(filenames),
        cols=1,
        shared_xaxes=True,
        subplot_titles=[
            f"{title} - <span style='font-size:10pt'>{filename}</span>"
            for title, filename in zip(titles, filenames)
        ],
        vertical_spacing=0.05,
    )

    for i, df in enumerate(data_list):
        for col in df.columns:
            if col not in ["timestamp", "relative_time"]:
                fig.add_trace(
                    go.Scatter(
                        x=df["relative_time"],
                        y=df[col],
                        name=col,
                        mode="lines",
                        legendgroup=col,  # Key to shared legend interactivity
                        showlegend=(i == 0),  # Only show legend once
                    ),
                    row=i + 1,
                    col=1,
                )

    fig.update_layout(
        height=900,
        title=master_title,
        xaxis3_title="Time (s)",
        yaxis_title="Sensor Value",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(t=60, b=80),
    )

    app = Dash(__name__)
    app.layout = html.Div(
        [
            dcc.Graph(id="my-graph", figure=fig),
            html.Button("Copy as PNG", id="copy-png-btn"),
            html.Div(id="copy-status"),
        ]
    )

    return app


if __name__ == "__main__":
    folder = "20250625 - lab testing data"
    filenames = [
        "E4B323F7C26C-20250625_113743-data",
        "E4B323F7CA50-20250625_113745-data",
        "E4B323F83080-20250625_113746-data",
    ]
    titles = ["Ambient", "ambient", "Lure"]
    app = create_dash_app(
        folder, filenames, titles, master_title="Settling Period 1 (5 minutes)"
    )
    app.run(debug=True)
