import pandas as pd
from ..state import DQState


def load_data_node(state: DQState) -> dict:
    """
    Load CSV data and parse DQ rules from the text file.

    Returns updated state with loaded data.
    """
    errors = []

    # Load CSV file
    try:
        df = pd.read_csv(state["csv_path"])
        dataframe_json = df.to_json(orient="records")
        columns = df.columns.tolist()
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
    except Exception as e:
        errors.append(f"Error loading CSV file: {str(e)}")
        dataframe_json = "[]"
        columns = []
        dtypes = {}

    # Load rules file
    try:
        with open(state["rules_path"], "r") as f:
            rules = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        errors.append(f"Error loading rules file: {str(e)}")
        rules = []

    return {
        "dataframe_json": dataframe_json,
        "columns": columns,
        "dtypes": dtypes,
        "rules": rules,
        "errors": errors,
    }
