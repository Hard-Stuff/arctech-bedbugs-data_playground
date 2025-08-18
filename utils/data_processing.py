import pandas as pd
from typing import List


def apply_moving_average(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Apply a simple moving average to all numeric columns except identifiers.
    Returns a DataFrame with the same structure.
    """
    numeric_cols = [
        c
        for c in df.columns
        if c not in ["timestamp", "relative_time", "device_id", "scenario"]
    ]

    smoothed_frames = []

    # If you have multiple scenarios, process each separately
    scenarios = df["scenario"].unique() if "scenario" in df.columns else ["default"]

    for scenario in scenarios:
        gdf = df[df["scenario"] == scenario] if scenario != "default" else df.copy()
        smoothed = gdf.copy()
        smoothed[numeric_cols] = (
            gdf[numeric_cols].rolling(window=window, min_periods=1).mean()
        )
        smoothed_frames.append(smoothed)

    combined = pd.concat(smoothed_frames, ignore_index=True)
    combined["device_id"] = df["device_id"].iloc[0]  # preserve device_id
    return combined


def take_last_n_samples(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Return only the last `n` rows of each scenario in the DataFrame.
    Preserves device_id and scenario structure.
    """
    frames = []
    scenarios = df["scenario"].unique() if "scenario" in df.columns else ["default"]

    for scenario in scenarios:
        gdf = df[df["scenario"] == scenario] if scenario != "default" else df.copy()
        frames.append(gdf.tail(n))

    combined = pd.concat(frames, ignore_index=True)
    combined["device_id"] = df["device_id"].iloc[0]
    return combined


def drop_columns(df: pd.DataFrame, cols_to_drop: List[str]) -> pd.DataFrame:
    """
    Drop columns from a DataFrame by partial substring match.

    Args:
        df: Input DataFrame.
        cols_to_drop: List of substrings. Any column containing one of these substrings
                      will be removed.

    Returns:
        A new DataFrame with the specified columns removed.
    """
    columns_to_remove = [
        col for col in df.columns if any(sub in col for sub in cols_to_drop)
    ]
    return df.drop(columns=columns_to_remove, errors="ignore")
