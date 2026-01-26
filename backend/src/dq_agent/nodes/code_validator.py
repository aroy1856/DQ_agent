"""
Code validator node - validates generated code before execution.
Performs AST analysis and LLM self-review.
"""
import ast
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import DQState


CODE_REVIEW_PROMPT = """You are a Python code reviewer specializing in data quality validation code.

Review the following code for:
1. **Security issues** - Any dangerous operations (file I/O, network, system calls)
2. **Logic errors** - Incorrect validation logic
3. **Edge cases** - Missing null checks, empty dataframe handling
4. **Output format** - Must return list of dicts with 'rule', 'passed', 'details' keys

Code to review:
```python
{code}
```

Rules being validated:
{rules}

Respond with a JSON object:
{{
    "is_valid": true/false,
    "issues": ["list of issues if any"],
    "suggestions": ["list of improvement suggestions"]
}}

If the code is safe and correct, set is_valid to true with empty issues.
Return ONLY the JSON object, no markdown formatting.
"""


class ASTValidator:
    """Validates Python code using AST analysis."""
    
    FORBIDDEN_NODES = (
        ast.Import,  # We check imports separately
        ast.ImportFrom,
    )
    
    ALLOWED_IMPORTS = {'pandas', 'pd', 're', 'json'}
    
    FORBIDDEN_CALLS = {
        'exec', 'eval', 'compile', 'open', 'input',
        '__import__', 'globals', 'locals', 'vars',
        'getattr', 'setattr', 'delattr',
        'os.system', 'subprocess', 'socket',
    }
    
    def __init__(self, code: str):
        self.code = code
        self.issues: list[str] = []
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate the code and return (is_valid, issues)."""
        try:
            tree = ast.parse(self.code)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]
        
        self._check_tree(tree)
        return len(self.issues) == 0, self.issues
    
    def _check_tree(self, tree: ast.AST):
        """Walk through the AST and check for issues."""
        for node in ast.walk(tree):
            # Check for forbidden function calls
            if isinstance(node, ast.Call):
                self._check_call(node)
            
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.ALLOWED_IMPORTS:
                        self.issues.append(f"Forbidden import: {alias.name}")
            
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] not in self.ALLOWED_IMPORTS:
                    self.issues.append(f"Forbidden import from: {node.module}")
            
            # Check for file operations
            if isinstance(node, ast.With):
                self.issues.append("'with' statement not allowed (potential file access)")
    
    def _check_call(self, node: ast.Call):
        """Check function calls for forbidden operations."""
        func_name = self._get_call_name(node)
        if func_name in self.FORBIDDEN_CALLS:
            self.issues.append(f"Forbidden function call: {func_name}")
    
    def _get_call_name(self, node: ast.Call) -> str:
        """Extract the function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return ""


def validate_with_ast(code: str) -> tuple[bool, list[str]]:
    """Validate code using AST analysis."""
    validator = ASTValidator(code)
    return validator.validate()


def validate_with_llm(code: str, rules: list[str]) -> tuple[bool, list[str], list[str]]:
    """Validate code using LLM self-review."""
    prompt = ChatPromptTemplate.from_template(CODE_REVIEW_PROMPT)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "code": code,
            "rules": "\n".join(f"- {r}" for r in rules),
        })
        
        content = response.content.strip()
        
        # Clean markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content.strip())
        
        is_valid = result.get("is_valid", False)
        issues = result.get("issues", [])
        suggestions = result.get("suggestions", [])
        
        return is_valid, issues, suggestions
        
    except Exception as e:
        # If LLM review fails, log but don't block execution
        return True, [], [f"LLM review skipped: {str(e)}"]


def code_validator_node(state: DQState) -> dict:
    """
    Validate generated code using AST analysis and LLM self-review.
    """
    errors = []
    
    code = state.get("generated_code", "")
    if not code:
        errors.append("No code to validate")
        return {"errors": errors, "validation_passed": False}
    
    # Get rules for LLM context
    all_rules = state.get("all_rules", [])
    rules = [r["text"] for r in all_rules] if all_rules else state.get("rules", [])
    
    # Step 1: AST validation
    ast_valid, ast_issues = validate_with_ast(code)
    if not ast_valid:
        errors.extend([f"AST: {issue}" for issue in ast_issues])
        return {
            "errors": errors,
            "validation_passed": False,
            "validation_details": {"ast_issues": ast_issues},
        }
    
    # Step 2: LLM self-review
    llm_valid, llm_issues, llm_suggestions = validate_with_llm(code, rules)
    
    if not llm_valid:
        errors.extend([f"LLM Review: {issue}" for issue in llm_issues])
        return {
            "errors": errors,
            "validation_passed": False,
            "validation_details": {
                "ast_issues": [],
                "llm_issues": llm_issues,
                "llm_suggestions": llm_suggestions,
            },
        }
    
    # Log suggestions for debugging
    if llm_suggestions:
        print(f"LLM suggestions: {llm_suggestions}")
    
    return {
        "validation_passed": True,
        "validation_details": {
            "ast_issues": [],
            "llm_issues": [],
            "llm_suggestions": llm_suggestions,
        },
    }
