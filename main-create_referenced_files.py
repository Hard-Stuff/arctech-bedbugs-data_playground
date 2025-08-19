from utils.file_openner import (
    load_and_prepare_data_with_reference,
    all_filenames_belonging_to_device,
)
from utils.data_processing import take_last_n_samples, drop_columns

from typing import Dict
from pandas import DataFrame
from pathlib import Path
import os

# DEFINITIONS
DEVICE_IDS = ["94A99037CBDC", "94A99037D910"]  # example devices
MASTER_FOLDER = "./scratch_data/20250813 - DEAD BEDBUG"

# OPERATION AND CONTROL
SHOW_ONLY_LAST_N_SAMPLES = 25  # Show only the last N samples on the graph
OUTPUT_FOLDER = f"{MASTER_FOLDER}/referenced"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# WORKING VARIABLES
data_dict: Dict[str, DataFrame] = {}

for device_id in DEVICE_IDS:
    # --- Get all control (empty petri dish) files ---
    control_files = all_filenames_belonging_to_device(
        device_id,
        MASTER_FOLDER,
        include_list=["EMPTY PETRI DISH"],  # only consider controls
        first_N=5,
    )

    if not control_files:
        raise ValueError(f"No control files found for device {device_id}")

    # Use the last control file as the reference
    control_file = control_files[-1]

    # --- Get all test files (exclude empty petri dish files) ---
    test_files = all_filenames_belonging_to_device(
        device_id,
        MASTER_FOLDER,
        skip_list=["EMPTY PETRI DISH"],  # exclude controls,
    )

    # --- Load & normalize test files using device-specific control ---
    df = load_and_prepare_data_with_reference(
        test_files,
        control_file,
        take_last_n=10,
    )

    if SHOW_ONLY_LAST_N_SAMPLES:
        df = take_last_n_samples(df, SHOW_ONLY_LAST_N_SAMPLES)

    data_dict[df["device_id"].iloc[0]] = df

if __name__ == "__main__":
    for device_id, df in data_dict.items():
        # Split by scenario
        for scenario, scenario_df in df.groupby("scenario"):
            export_df = drop_columns(scenario_df, ["scenario", "device_id", "_R1"]).copy()

            # Add legacy timestamp column
            export_df = export_df.rename(columns={"relative_time": "timestamp_s"})

            # Sanitize scenario name for filename
            sanitized_scenario = str(scenario).replace("/", "_")

            # Save one CSV per device per scenario
            filename = f"{sanitized_scenario} ({device_id}).csv"
            filepath = Path(OUTPUT_FOLDER) / filename
            export_df.to_csv(filepath, index=False)
            print(f"Saved {filepath}")
