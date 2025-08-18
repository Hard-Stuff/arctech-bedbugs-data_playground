from utils.n_plot import create_dash_app
from utils.file_openner import (
    load_and_prepare_data_with_reference,
    all_filenames_belonging_to_device,
)
from utils.data_processing import (
    apply_moving_average,
    take_last_n_samples,
    drop_columns,
)

DEVICE_IDS = ["94A99037CBDC", "94A99037D910"]  # example devices
MASTER_FOLDER = "./scratch_data/20250813 - DEAD BEDBUG"

data_dict = {}

for device_id in DEVICE_IDS:
    # --- Get all control (empty petri dish) files ---
    control_files = all_filenames_belonging_to_device(
        device_id,
        MASTER_FOLDER,
        include_list=["EMPTY PETRI DISH"],  # only consider controls
        first_N=5
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

    # --- Load & normalize test files using device-specific control ---
    df = load_and_prepare_data_with_reference(
        test_files,
        control_file,  # device-specific reference
        take_last_n=10,
    )

    # --- Standard preprocessing ---
    df = drop_columns(df, ["BME688", "SGP41", "_R1"])
    df = take_last_n_samples(df, 25)
    df = apply_moving_average(df, 5)

    data_dict[df["device_id"].iloc[0]] = df

# --- Create Dash App ---
titles = {device_id: f"Device {device_id}" for device_id in data_dict.keys()}

app = create_dash_app(
    data_dict,
    titles=titles,
    master_title="Sensor Comparison: Normalized to Device-Specific Controls",
)

if __name__ == "__main__":
    app.run(debug=True)
