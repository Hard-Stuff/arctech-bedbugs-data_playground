import pandas as pd
import os
import re
from typing import List, Optional, Dict


def extract_device_id(filename: str) -> str:
    """Extract device_id from '(DEVICEID)-' in the filename."""
    match = re.search(r"\((.*?)\)-", os.path.basename(filename))
    return match.group(1) if match else os.path.basename(filename)


def extract_scenario(filename: str) -> str:
    """Extract scenario/condition from filename, ignoring device_id and date."""
    base = os.path.basename(filename)
    # Remove device ID + timestamp
    scenario = re.sub(r"\s*\(.*?\)-\d+.*\.csv$", "", base)
    return scenario.strip()


def all_filenames_belonging_to_device(
    device_id: str,
    folder: str,
    first_N: Optional[int] = None,
    skip_list: Optional[List[str]] = None,
    include_list: Optional[List[str]] = None,
) -> List[str]:
    """
    Return all filenames in `folder` that contain `device_id` in their name,
    sorted naturally, optionally skipping files containing any substring in skip_list,
    and optionally requiring at least one substring in include_list to be present.

    Parameters
    ----------
    device_id : str
        The device ID to search for in filenames.
    folder : str
        Folder to search in.
    first_N : Optional[int]
        If specified, only return the first N matching files.
    skip_list : Optional[List[str]]
        List of substrings; any filename containing one of these will be ignored.
    include_list : Optional[List[str]]
        List of substrings; at least one must appear in the filename to include it.

    Returns
    -------
    List[str]
        Full paths to matching files.
    """

    skip_list = skip_list or []
    include_list = include_list or []

    def natural_sort_key(s: str):
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split(r"(\d+)", s)
        ]

    matching_files = []
    for filename in sorted(os.listdir(folder), key=natural_sort_key):
        if device_id not in filename:
            continue
        if any(skip_str in filename for skip_str in skip_list):
            continue
        if include_list and not any(inc_str in filename for inc_str in include_list):
            continue

        full_path = os.path.join(folder, filename)
        if os.path.isfile(full_path):
            matching_files.append(full_path)

        if first_N is not None and len(matching_files) >= first_N:
            break

    return matching_files


def load_and_prepare_data(filenames: List[str]) -> pd.DataFrame:
    """
    Load CSVs for a single device, clean, and return combined DataFrame
    with device_id and scenario labels.
    """
    frames = []
    device_id = None

    for file in filenames:
        df = pd.read_csv(file)

        # Drop last column (timestamp_s)
        df = df.iloc[:, :-1].reset_index(drop=True)

        # Add relative_time (s)
        df["relative_time"] = (df["timestamp"] - df["timestamp"].iloc[0]) / 1000.0

        # Extract once
        if device_id is None:
            device_id = extract_device_id(file)

        # Scenario condition
        df["scenario"] = extract_scenario(file)

        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined["device_id"] = device_id

    return combined


# Default: simple division
DEFAULT_NORMALIZE_FN = lambda col_values, ref_value: (
    col_values / ref_value if ref_value != 0 else col_values
)


def load_and_prepare_data_with_reference(
    filenames: List[str],
    reference: str,
    take_last_n: int = -1,
    normalize_cols: Optional[List[str]] = None,
    normalize_fn=DEFAULT_NORMALIZE_FN,
) -> pd.DataFrame:
    """
    Load CSVs for a single device, normalize against reference,
    and return combined DataFrame with device_id and scenario labels.
    """
    if normalize_cols is None:
        normalize_cols = [
            "BME688_R",
            "ENS160_R0",
            "ENS160_R1",
            "ENS160_R2",
            "ENS160_R3",
        ]

    # --- Reference averages ---
    ref_df = pd.read_csv(reference).iloc[:, :-1]
    if take_last_n > 0:
        ref_df = ref_df.tail(take_last_n)
    ref_means = ref_df[normalize_cols].mean()

    frames = []
    device_id = extract_device_id(reference)

    for file in filenames:
        df = pd.read_csv(file).iloc[:, :-1].reset_index(drop=True)

        # relative_time
        df["relative_time"] = (df["timestamp"] - df["timestamp"].iloc[0]) / 1000.0

        # Apply normalization function
        for col in normalize_cols:
            if col in df.columns:
                df[col] = normalize_fn(df[col], ref_means[col])

        # Scenario
        df["scenario"] = extract_scenario(file)

        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined["device_id"] = device_id

    return combined
