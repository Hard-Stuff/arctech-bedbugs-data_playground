from utils.n_plot import create_per_device_app, create_grouped_app
from utils.file_openner import (
    load_and_prepare_data_with_reference,
    load_and_prepare_data,
    all_filenames_belonging_to_device,
)
from utils.data_processing import (
    apply_moving_average,
    take_last_n_samples,
    drop_columns,
)

from typing import Dict
from pandas import DataFrame

# DEFINITIONS
DEVICE_IDS = ["94A99037CBDC", "94A99037D910"]  # example devices
MASTER_FOLDER = "./scratch_data/20250813 - DEAD BEDBUG"

# OPERATION AND CONTROL

USE_REFERENCING_TO_NORMALISE = False  # We use the last "EMPTY PETRI DISH" files to normalise the data
SHOW_RAW_LINES_NOT_BANDS = False  # Takes the average of a scenario (a given set of exposures by name) and plots that over the ghost of all instead.
SHOW_ONLY_LAST_N_SAMPLES = 25  # Show only the last N samples on the graph

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
        # first_N=10
    )

    if USE_REFERENCING_TO_NORMALISE:
        # --- Load & normalize test files using device-specific control ---
        df = load_and_prepare_data_with_reference(
            test_files,
            control_file,  # device-specific reference
            take_last_n=10,
        )
    else:
        df = load_and_prepare_data(test_files)

    # --- Standard preprocessing ---
    df = drop_columns(df, ["BME688", "SGP41", "_R1"])

    if SHOW_ONLY_LAST_N_SAMPLES:
        df = take_last_n_samples(df, SHOW_ONLY_LAST_N_SAMPLES)

    df = apply_moving_average(df, 5)

    data_dict[df["device_id"].iloc[0]] = df

# --- Create Dash App ---
titles = {device_id: f"Device {device_id}" for device_id in data_dict.keys()}

if SHOW_RAW_LINES_NOT_BANDS:
    app = create_per_device_app(
        data_dict,
        titles=titles,
        master_title="Sensor Comparison: Normalized to Device-Specific Controls",
    )
else:
    app = create_grouped_app(
        data_dict,
        master_title="Sensor Comparison: Normalized to Device-Specific Controls",
    )

if __name__ == "__main__":
    app.run(debug=True)
