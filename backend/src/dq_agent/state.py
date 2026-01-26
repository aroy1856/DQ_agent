from typing import TypedDict, Annotated, Literal
import operator


class Rule(TypedDict):
    """A data quality rule with source tracking."""
    id: str
    text: str
    source: Literal["user", "llm"]


class DQState(TypedDict):
    """State schema for the DQ Agent graph."""

    # Input paths
    csv_path: str
    rules_path: str

    # Loaded data
    rules: list[str]  # Original user rules (text only)
    all_rules: list[Rule]  # All rules with source tags (user + llm)
    dataframe_json: str  # JSON representation of DataFrame
    columns: list[str]
    dtypes: dict[str, str]
    metadata: str  # User-provided column metadata/descriptions

    # Processing
    generated_code: str
    execution_results: list[dict]

    # Output
    final_report: str
    errors: Annotated[list[str], operator.add]

