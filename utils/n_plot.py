import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from typing import List, Optional, Dict, Union
import plotly.express as px
import plotly.colors as pc


def create_dash_app(
    data_dict: Dict[str, pd.DataFrame],
    titles: Optional[Union[Dict[str, str], List[str]]] = None,
    master_title: str = "Sensor Comparison Dashboard",
):
    """
    Dash app for visualizing multiple device DataFrames with scenarios,
    dynamic sensor selection, and distinct colors per trace.
    """
    device_ids = list(data_dict.keys())

    # --- Handle titles ---
    if titles is None:
        use_titles = {device_id: device_id for device_id in device_ids}
    elif isinstance(titles, dict):
        use_titles = {
            device_id: titles.get(device_id, device_id) for device_id in device_ids
        }
    elif isinstance(titles, list):
        if len(titles) != len(device_ids):
            raise ValueError("Length of titles list must match number of devices")
        use_titles = {device_id: title for device_id, title in zip(device_ids, titles)}
    else:
        raise TypeError("titles must be None, dict, or list")

    # --- Determine layout ---
    n_rows = len(device_ids)
    screen_height = 1200
    height_per_row = screen_height if n_rows == 1 else max(300, screen_height / n_rows)
    vertical_spacing = 0.05 if n_rows > 1 else 0.0

    # --- Gather all unique sensor columns ---
    all_sensors = set()
    for df in data_dict.values():
        all_sensors.update(
            [
                c
                for c in df.columns
                if c not in ["timestamp", "relative_time", "device_id", "scenario"]
            ]
        )
    all_sensors = sorted(list(all_sensors))  # deterministic order

    # --- Color palette ---
    colors = px.colors.qualitative.Plotly
    color_cycle = colors * ((len(all_sensors) * n_rows // len(colors)) + 1)
    all_sensor_cols = [
        c
        for df in data_dict.values()
        for c in df.columns
        if c not in ["timestamp", "relative_time", "device_id", "scenario"]
    ]
    all_sensor_cols = sorted(list(set(all_sensor_cols)))
    sensor_to_color = {
        col: color_cycle[i % len(color_cycle)] for i, col in enumerate(all_sensor_cols)
    }

    # --- Create figure ---
    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=True,
        subplot_titles=[
            f"{use_titles.get(device_id, device_id)} - <span style='font-size:10pt'>{device_id}</span>"
            for device_id in device_ids
        ],
        vertical_spacing=vertical_spacing,
    )

    trace_idx = 0
    for row_idx, device_id in enumerate(device_ids, start=1):
        df = data_dict[device_id]
        scenarios = df["scenario"].unique() if "scenario" in df.columns else ["default"]

        for scenario_idx, scenario in enumerate(scenarios):

            gdf = df[df["scenario"] == scenario] if scenario != "default" else df
            for col in [
                c
                for c in gdf.columns
                if c not in ["timestamp", "relative_time", "device_id", "scenario"]
            ]:

                base_color = sensor_to_color[col]  # color per sensor
                rgb = pc.hex_to_rgb(base_color)
                factor = 0.2 + 0.8 * scenario_idx / max(1, len(scenarios) - 1)
                shaded_color = f"rgb({int(rgb[0]*factor)}, {int(rgb[1]*factor)}, {int(rgb[2]*factor)})"
                fig.add_trace(
                    go.Scatter(
                        x=gdf["relative_time"],
                        y=gdf[col],
                        name=f"{scenario} - {col}",
                        mode="lines",
                        legendgroup=f"{col}",  # group by sensor for toggling
                        line=dict(color=shaded_color),
                        showlegend=(row_idx == 1),
                    ),
                    row=row_idx,
                    col=1,
                )
                trace_idx += 1

    fig.update_layout(
        height=height_per_row * n_rows,
        title=master_title,
        xaxis_title="Time (s)",
        yaxis_title="Sensor Value",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(t=60, b=80),
    )

    # --- Dash App ---
    app = Dash(__name__)
    app.layout = html.Div(
        [
            dcc.Graph(id="my-graph", figure=fig),
            html.Button("Copy as PNG", id="copy-png-btn"),
            html.Div(id="copy-status"),
        ]
    )

    return app
