import argparse
import os
from dotenv import load_dotenv

from src.dq_agent import dq_graph


def main():
    """Main entry point for the DQ Agent."""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Data Quality Agent - Check CSV data against DQ rules"
    )
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to the CSV file to check",
    )
    parser.add_argument(
        "--rules",
        type=str,
        required=True,
        help="Path to the text file containing DQ rules (one rule per line)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional: Path to save the report (prints to console if not specified)",
    )

    args = parser.parse_args()

    # Validate input files exist
    if not os.path.exists(args.csv):
        print(f"Error: CSV file not found: {args.csv}")
        return 1

    if not os.path.exists(args.rules):
        print(f"Error: Rules file not found: {args.rules}")
        return 1

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key in a .env file or environment variable")
        return 1

    print("Starting Data Quality Check...")
    print(f"CSV File: {args.csv}")
    print(f"Rules File: {args.rules}")
    print("-" * 40)

    # Run the DQ graph
    initial_state = {
        "csv_path": args.csv,
        "rules_path": args.rules,
        "rules": [],
        "dataframe_json": "",
        "columns": [],
        "dtypes": {},
        "generated_code": "",
        "execution_results": [],
        "final_report": "",
        "errors": [],
    }

    try:
        result = dq_graph.invoke(initial_state)

        # Print the final report
        print(result.get("final_report", "No report generated"))

        # Optionally save to file
        if args.output:
            with open(args.output, "w") as f:
                f.write(result.get("final_report", "No report generated"))
            print(f"\nReport saved to: {args.output}")

        return 0

    except Exception as e:
        print(f"Error running DQ Agent: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
