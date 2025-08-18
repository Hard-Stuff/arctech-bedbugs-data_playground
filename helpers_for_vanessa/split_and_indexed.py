import os
import pandas as pd


def split_and_indexed(input_folder: str, end_strip: int = 30):
    output_folder = f"{input_folder} - split and indexed"
    os.makedirs(output_folder, exist_ok=True)
    # Process each CSV file in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            input_path = os.path.join(input_folder, filename)
            df = pd.read_csv(input_path)

            # Keep only the last 30 rows
            df = df.tail(end_strip).reset_index(drop=True)

            # Remove the last column (assumed to be 'timestamp_ms')
            df = df.iloc[:, :-1]

            # Add index column from 1 to 30 at the front
            df.insert(0, "index", range(1, len(df) + 1))

            # Save the modified DataFrame to the output folder
            output_path = os.path.join(output_folder, filename)
            df.to_csv(output_path, index=False)

    print("Normalization complete. Files saved in:", output_folder)


if __name__ == "__main__":
    split_and_indexed(input_folder=r"data\20250709 - Bedbug")
