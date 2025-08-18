import json
from utils.n_plot import create_dash_app
from utils.file_openner import load_and_prepare_data, all_filenames_belonging_to_device

# Step 1 - load in all relevant data for a single device
DEVICE_ID = "94A99037CBDC"
CONTROL_PREFIX = "EMPTY PETRI DISH"

# Step 2 - figure out the avg. values to use as our reference point
# (TODO - hook in load_and_prepare_data_with_reference if needed)

# Get files for a specific device
filenames = all_filenames_belonging_to_device(
    "94A99037D910", "./scratch_data/20250813 - DEAD BEDBUG", 10, ["EMPTY PETRI DISH"]
)

df = load_and_prepare_data(filenames)

app = create_dash_app(
    {df["device_id"].iloc[0]: df},  # wrap single DataFrame in dict for plotting
    titles={df["device_id"].iloc[0]: "Settling Period 1 (5 minutes)"},
    master_title="Sensor Comparison Dashboard",
)

if __name__ == "__main__":
    app.run(debug=True)
