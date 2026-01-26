"""
Rule generator node - uses LLM to suggest DQ rules based on dataset metadata.
"""
import json
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import DQState


RULE_GENERATION_PROMPT = """You are a data quality expert. Based on the following dataset metadata, suggest relevant data quality rules.

Dataset Information:
- Columns: {columns}
- Data types: {dtypes}
- Sample data (first few rows): {sample_data}

Column Metadata (user-provided descriptions):
{column_metadata}

User-provided rules (if any):
{user_rules}

Generate additional data quality rules that would be valuable for this dataset. Consider:
1. Column metadata descriptions (if provided) - these describe what each column should contain
2. Column name patterns (e.g., "email" → email format validation)
3. Data types (e.g., numeric columns → range checks, null checks)
4. Common data quality checks (uniqueness, completeness, format validation)
5. Patterns visible in sample data

IMPORTANT:
- Do NOT duplicate any user-provided rules
- Generate 3-5 NEW rules that complement the existing ones
- Each rule should be a clear, actionable statement
- Focus on rules that are likely to catch real data quality issues
- Use the column metadata to generate more accurate rules

Return ONLY a JSON array of rule strings, no explanations.
Example format: ["Check that 'status' column only contains valid values", "Ensure 'date' column is in valid date format"]
"""


def rule_generator_node(state: DQState) -> dict:
    """
    Generate suggested DQ rules using LLM based on dataset metadata.
    Returns rules with source tags (user/llm) and unique IDs.
    """
    errors = []
    all_rules = []

    # Convert existing user rules to tagged format
    user_rules = state.get("rules", [])
    for rule_text in user_rules:
        all_rules.append({
            "id": str(uuid.uuid4()),
            "text": rule_text,
            "source": "user",
        })

    # Prepare sample data
    try:
        all_data = json.loads(state.get("dataframe_json", "[]"))
        sample_data = json.dumps(all_data[:5], indent=2)
    except Exception:
        sample_data = "[]"

    # Prepare user rules text for prompt
    user_rules_text = "\n".join(f"- {r}" for r in user_rules) if user_rules else "None provided"
    
    # Get column metadata if provided
    column_metadata = state.get("metadata", "") or "None provided"

    prompt = ChatPromptTemplate.from_template(RULE_GENERATION_PROMPT)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    chain = prompt | llm

    try:
        response = chain.invoke({
            "columns": state["columns"],
            "dtypes": state["dtypes"],
            "sample_data": sample_data,
            "column_metadata": column_metadata,
            "user_rules": user_rules_text,
        })

        # Parse the LLM response
        content = response.content.strip()
        
        # Clean up markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # Parse JSON array of rules
        generated_rules = json.loads(content)
        
        if isinstance(generated_rules, list):
            for rule_text in generated_rules:
                if isinstance(rule_text, str) and rule_text.strip():
                    all_rules.append({
                        "id": str(uuid.uuid4()),
                        "text": rule_text.strip(),
                        "source": "llm",
                    })

        print(f"Generated {len(generated_rules)} LLM rules")

    except json.JSONDecodeError as e:
        errors.append(f"Failed to parse LLM response as JSON: {str(e)}")
    except Exception as e:
        errors.append(f"Error generating rules: {str(e)}")

    return {
        "all_rules": all_rules,
        "errors": state.get("errors", []) + errors,
    }
