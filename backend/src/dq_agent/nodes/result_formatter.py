from datetime import datetime
from ..state import DQState


def result_formatter_node(state: DQState) -> dict:
    """
    Format execution results into a comprehensive DQ report.
    """
    results = state.get("execution_results", [])
    errors = state.get("errors", [])

    # Build the report
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("DATA QUALITY CHECK REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"CSV File: {state.get('csv_path', 'N/A')}")
    report_lines.append(f"Rules File: {state.get('rules_path', 'N/A')}")
    report_lines.append("")

    # Summary section
    if results:
        passed_count = sum(1 for r in results if r.get("passed", False))
        failed_count = len(results) - passed_count

        report_lines.append("-" * 60)
        report_lines.append("SUMMARY")
        report_lines.append("-" * 60)
        report_lines.append(f"Total Rules Checked: {len(results)}")
        report_lines.append(f"Passed: {passed_count}")
        report_lines.append(f"Failed: {failed_count}")
        report_lines.append("")

        # Detailed results
        report_lines.append("-" * 60)
        report_lines.append("DETAILED RESULTS")
        report_lines.append("-" * 60)

        for i, result in enumerate(results, 1):
            status = "✅ PASSED" if result.get("passed", False) else "❌ FAILED"
            report_lines.append(f"\nRule {i}: {result.get('rule', 'Unknown rule')}")
            report_lines.append(f"Status: {status}")
            report_lines.append(f"Details: {result.get('details', 'No details available')}")

    else:
        report_lines.append("No validation results available.")

    # Errors section
    if errors:
        report_lines.append("")
        report_lines.append("-" * 60)
        report_lines.append("ERRORS")
        report_lines.append("-" * 60)
        for error in errors:
            report_lines.append(f"• {error}")

    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 60)

    final_report = "\n".join(report_lines)

    return {"final_report": final_report}
