import json
import re
import builtins
import pandas as pd
from ..state import DQState


def code_executor_node(state: DQState) -> dict:
    """
    Safely execute the generated Python code and capture results.
    """
    errors = []
    execution_results = []

    if not state.get("generated_code"):
        errors.append("No generated code to execute")
        return {"execution_results": [], "errors": errors}

    # Reconstruct DataFrame from JSON
    try:
        data = json.loads(state["dataframe_json"])
        df = pd.DataFrame(data)
    except Exception as e:
        errors.append(f"Error reconstructing DataFrame: {str(e)}")
        return {"execution_results": [], "errors": errors}

    # Allowed modules for import
    allowed_modules = {
        "re": re,
        "json": json,
        "pandas": pd,
        "pd": pd,
    }

    def safe_import(name, *args, **kwargs):
        """Custom import that only allows specific modules."""
        if name in allowed_modules:
            return allowed_modules[name]
        raise ImportError(f"Import of '{name}' is not allowed")

    # Create a copy of builtins with our safe import
    safe_builtins = dict(vars(builtins))
    safe_builtins["__import__"] = safe_import

    # Define globals for execution
    safe_globals = {
        "__builtins__": safe_builtins,
        "pd": pd,
        "re": re,
    }

    local_vars = {}

    try:
        # Execute the generated code
        exec(state["generated_code"], safe_globals, local_vars)

        # Check if the validation function was created
        if "validate_dq_rules" not in local_vars:
            errors.append(
                "Generated code did not define 'validate_dq_rules' function"
            )
            return {"execution_results": [], "errors": errors}

        # Run the validation function
        validate_func = local_vars["validate_dq_rules"]
        execution_results = validate_func(df)

        # Validate the output format
        if not isinstance(execution_results, list):
            execution_results = [execution_results]

    except SyntaxError as e:
        errors.append(f"Syntax error in generated code: {str(e)}")
    except Exception as e:
        errors.append(f"Error executing generated code: {str(e)}")

    return {"execution_results": execution_results, "errors": errors}
