from utils.n_plot import create_per_device_app
from utils.file_opener import (
    load_and_prepare_data_with_reference,
    all_filenames_belonging_to_device,
)
from utils.data_processing import apply_moving_average, take_last_n_samples, drop_columns


# Simple division
NORMALIZATION_FUNCTION = lambda col_values, ref_value: (col_values / ref_value if ref_value != 0 else col_values)
# Simple subtraction
# NORMALIZATION_FUNCTION = lambda col_values, ref_value: (col_values - ref_value if ref_value != 0 else col_values)


# Step 1 - load in all relevant data for a single device
DEVICE_ID = "94A99037CBDC"
CONTROL_PREFIX = "EMPTY PETRI DISH"

# Get files for a specific device
filenames = all_filenames_belonging_to_device(
    "94A99037D910", "./scratch_data/20250813 - DEAD BEDBUG", 10, ["EMPTY PETRI DISH"]
)

# Step 2 - figure out the avg. values to use as our reference point
df = load_and_prepare_data_with_reference(
    filenames,
    "./scratch_data/20250813 - DEAD BEDBUG/Exposure 5 -EMPTY PETRI DISH  (94A99037D910)-20250813_104225.csv",
    10,
    normalize_fn=NORMALIZATION_FUNCTION
)

# Step 3 - apply modifications as desired

df = drop_columns(df, ["BME688", "SGP41", "_R1"])

df = take_last_n_samples(df, 25)

df = apply_moving_average(df, 5)

# Step 4 - create and show app
app = create_per_device_app(
    {df["device_id"].iloc[0]: df},  # wrap single DataFrame in dict for plotting
    titles={df["device_id"].iloc[0]: "Settling Period 1 (5 minutes)"},
    master_title="Sensor Comparison Dashboard",
)

if __name__ == "__main__":
    app.run(debug=True)
