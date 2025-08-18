import json
from utils.n_plot import create_dash_app

# Load tests.json
with open("tests.json", "r") as f:
    tests = json.load(f)

# Choose the test you want to run
test_key = "Bedbugs, background, Lure (2)"

test_data = tests[test_key]
folder = "20250625 - lab testing data"
filenames = [f for f in test_data["filenames"]]  # add .csv as you mentioned
titles = test_data["conditions"]
chambers = test_data["chambers"]

app = create_dash_app(
    folder=folder,
    filenames=filenames,
    titles=list(f"{titles[i]}:{chambers[i]}" for i in range(0, len(titles))),
    master_title=test_key,
)

if __name__ == "__main__":
    app.run(debug=True)
