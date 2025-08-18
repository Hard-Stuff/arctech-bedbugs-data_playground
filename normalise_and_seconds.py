import os
import pandas as pd

# Define input and output folders
input_folder = "data/20250701 to 20250702"
output_folder = "data/20250701 to 20250702 - normalised seconds"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Process each CSV file in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".csv"):
        input_path = os.path.join(input_folder, filename)
        df = pd.read_csv(input_path)

        # Normalize the timestamp
        first_timestamp = df["timestamp"].iloc[0]
        df["timestamp_s"] = ((
            df["timestamp"] - first_timestamp
        ) / 1000).astype(int)  # convert ms to seconds

        # Save the modified DataFrame to the output folder
        output_path = os.path.join(output_folder, filename)
        df.to_csv(output_path, index=False)

print("Normalization complete. Files saved in:", output_folder)
