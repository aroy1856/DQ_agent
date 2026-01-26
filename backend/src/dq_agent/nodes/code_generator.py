from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import DQState


CODE_GENERATION_PROMPT = """You are a Python expert that generates data quality validation code.

Given the following information about a pandas DataFrame:
- Columns: {columns}
- Data types: {dtypes}
- Sample data (first few rows in JSON format): {sample_data}

Column Metadata (descriptions of what each column should contain):
{column_metadata}

And the following data quality rules to validate:
{rules}

Generate a Python function called `validate_dq_rules` that:
1. Takes a pandas DataFrame as input
2. Validates each rule against the DataFrame
3. Returns a list of dictionaries, where each dictionary contains:
   - "rule": The original rule text
   - "passed": Boolean indicating if the rule passed
   - "details": String with details about the validation result (count of violations, specific issues, etc.)

Important guidelines:
- Use pandas operations for efficient validation
- Handle edge cases (empty columns, null values where appropriate)
- For email validation, use a simple regex pattern
- For numeric range checks, handle NaN values appropriately
- Include the count of violations in the details
- Use the column metadata to understand the expected format/values for each column

Return ONLY the Python code, no explanations or markdown formatting.
The code should be directly executable with exec().
"""


def code_generator_node(state: DQState) -> dict:
    """
    Generate Python validation code using LLM based on rules and DataFrame schema.
    """
    errors = []

    # Use all_rules if available (with source tags), otherwise fall back to rules
    all_rules = state.get("all_rules", [])
    if not all_rules and not state.get("rules"):
        errors.append("No rules found to generate code for")
        return {"generated_code": "", "errors": errors}

    # Extract rule text from all_rules (which contains {id, text, source})
    if all_rules:
        rules_list = [rule["text"] for rule in all_rules]
    else:
        rules_list = state["rules"]

    # Prepare the prompt
    rules_text = "\n".join(f"- {rule}" for rule in rules_list)

    # Get sample data (limit to first 5 rows for context)
    import json

    try:
        all_data = json.loads(state["dataframe_json"])
        sample_data = json.dumps(all_data[:5], indent=2)
    except Exception:
        sample_data = "[]"

    # Get column metadata
    column_metadata = state.get("metadata", "") or "None provided"

    prompt = ChatPromptTemplate.from_template(CODE_GENERATION_PROMPT)

    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    chain = prompt | llm

    try:
        response = chain.invoke(
            {
                "columns": state["columns"],
                "dtypes": state["dtypes"],
                "sample_data": sample_data,
                "column_metadata": column_metadata,
                "rules": rules_text,
            }
        )
        generated_code = response.content

        # Clean up the code if it has markdown formatting
        if generated_code.startswith("```python"):
            generated_code = generated_code[9:]
        if generated_code.startswith("```"):
            generated_code = generated_code[3:]
        if generated_code.endswith("```"):
            generated_code = generated_code[:-3]

        generated_code = generated_code.strip()

        print(generated_code)

    except Exception as e:
        errors.append(f"Error generating code: {str(e)}")
        generated_code = ""

    return {"generated_code": generated_code, "errors": errors}
