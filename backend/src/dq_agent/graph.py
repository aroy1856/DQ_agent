from langgraph.graph import StateGraph, END

from .state import DQState
from .nodes import (
    load_data_node,
    code_generator_node,
    code_executor_node,
    result_formatter_node,
)


def create_dq_graph():
    """
    Create and compile the DQ Agent graph.

    The graph follows this flow:
    1. Load Data & Rules -> Read CSV and parse rules file
    2. Code Generator -> Generate Python validation code using LLM
    3. Code Executor -> Execute the generated code safely
    4. Result Formatter -> Format results into a readable report
    """
    # Create the graph
    workflow = StateGraph(DQState)

    # Add nodes
    workflow.add_node("load_data", load_data_node)
    workflow.add_node("code_generator", code_generator_node)
    workflow.add_node("code_executor", code_executor_node)
    workflow.add_node("result_formatter", result_formatter_node)

    # Define edges (linear flow)
    workflow.set_entry_point("load_data")
    workflow.add_edge("load_data", "code_generator")
    workflow.add_edge("code_generator", "code_executor")
    workflow.add_edge("code_executor", "result_formatter")
    workflow.add_edge("result_formatter", END)

    # Compile the graph
    graph = workflow.compile()

    return graph


# Export the compiled graph
dq_graph = create_dq_graph()
