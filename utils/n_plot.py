import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html
import re
from typing import List, Optional, Dict, Union
import plotly.express as px
import plotly.colors as pc
import numpy as np


def create_per_device_app(
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
        use_titles = {device_id: titles.get(device_id, device_id) for device_id in device_ids}
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
        all_sensors.update([c for c in df.columns if c not in ["timestamp", "relative_time", "device_id", "scenario"]])
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
    sensor_to_color = {col: color_cycle[i % len(color_cycle)] for i, col in enumerate(all_sensor_cols)}

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
            for col in [c for c in gdf.columns if c not in ["timestamp", "relative_time", "device_id", "scenario"]]:

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


def create_grouped_app(
    data_dict: Dict[str, pd.DataFrame],
    master_title: str = "Scenario Grouped Comparison Dashboard",
):
    """
    Dash app for visualizing multiple device DataFrames on a single plot.
    Groups exposures by scenario, shows replicates as shaded spreads,
    and group means as colored lines (no resampling).
    """
    combined = pd.concat(data_dict.values(), ignore_index=True)

    if "scenario" not in combined.columns:
        raise ValueError("DataFrames must contain a 'scenario' column to group exposures")

    # --- Extract exposure number + scenario base ---
    exp_re = r"Exposure\s*(\d+)\s*-\s*(.*)"
    combined[["exposure_num", "scenario_base"]] = combined["scenario"].str.extract(exp_re)
    combined["exposure_num"] = combined["exposure_num"].astype(float)

    # Build scenario_group = "Exposure (min–max) - scenario_base"
    grouped_labels = {}
    for base, gdf in combined.groupby("scenario_base"):
        nums = sorted(gdf["exposure_num"].dropna().unique())
        if len(nums) > 0:
            label = f"Exposure ({int(min(nums))}–{int(max(nums))}) - {base}"
        else:
            label = f"Exposure - {base}"
        grouped_labels[base] = label
    combined["scenario_group"] = combined["scenario_base"].map(grouped_labels)

    # --- Sensors ---
    device_ids = list(data_dict.keys())
    sensors = [
        c
        for c in combined.columns
        if c
        not in [
            "timestamp",
            "relative_time",
            "device_id",
            "scenario",
            "scenario_group",
            "exposure_num",
            "scenario_base",
        ]
    ]

    # --- Color mapping (sensor + scenario) ---
    colors = px.colors.qualitative.Plotly
    color_cycle = colors * ((len(sensors) * len(grouped_labels) // len(colors)) + 1)
    combo_keys = []
    for sensor in sensors:
        for group in grouped_labels.values():
            combo_keys.append((sensor, group))
    sensor_scenario_to_color = {key: color_cycle[i % len(color_cycle)] for i, key in enumerate(combo_keys)}

    # --- Figure ---
    fig = go.Figure()

    for sensor in sensors:
        for group_name, gdf in combined.groupby("scenario_group"):
            pivoted = gdf.pivot_table(index="relative_time", columns="scenario", values=sensor)

            if pivoted.empty:
                continue

            # Convert to numpy arrays directly
            values = pivoted.to_numpy(dtype=float)
            time_axis = pivoted.index.to_numpy(dtype=float)

            mean_series = np.nanmean(values, axis=1)
            min_series = np.nanmin(values, axis=1)
            max_series = np.nanmax(values, axis=1)

            base_color = sensor_scenario_to_color[(sensor, group_name)]
            rgb = pc.hex_to_rgb(base_color)
            shaded_color = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.2)"

            # Spread band
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=max_series,
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip",
                    fill=None,
                    legendgroup=sensor,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=min_series,
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip",
                    fill="tonexty",
                    fillcolor=shaded_color,
                    legendgroup=sensor,
                )
            )

            # Mean line (legend shown once per sensor+group)
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=mean_series,
                    mode="lines",
                    name=f"{group_name} - {sensor}",
                    line=dict(color=base_color, width=2),
                    legendgroup=sensor,
                    showlegend=True,
                )
            )
    device_list_str = ", ".join(device_ids)
    fig.update_layout(
        height=900,
        title=f"{master_title} — Sensors: {device_list_str}",
        xaxis_title="Time (s)",
        yaxis_title="Sensor Value",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(t=60, b=80),
    )

    # --- Dash app ---
    app = Dash(__name__)
    app.layout = html.Div([dcc.Graph(id="my-graph", figure=fig)])
    return app
