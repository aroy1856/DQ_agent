"""
Rules and validation pipeline routes for the DQ Agent API.
"""
import os
import json
import tempfile
import asyncio
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from src.dq_agent.nodes import (
    load_data_node,
    code_generator_node,
    code_validator_node,
    code_executor_node,
    result_formatter_node,
    rule_generator_node,
)
from src.dq_agent.thread_manager import thread_manager
from src.dq_agent.api.models import RuleModel, RulesLoadedResponse, RulesUpdateRequest
from src.dq_agent.api.utils import safe_json_dumps


router = APIRouter()


@router.post("/{thread_id}/load-rules", response_model=RulesLoadedResponse)
async def load_rules(
    thread_id: str,
    csv_file: UploadFile = File(...),
    rules_file: Optional[UploadFile] = File(None),
    rules: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    metadata_file: Optional[UploadFile] = File(None),
):
    """Load CSV and rules, generate AI suggestions, return all rules for review."""
    if thread_manager.get_thread(thread_id) is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    try:
        # Save CSV
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp_csv:
            content = await csv_file.read()
            tmp_csv.write(content)
            csv_path = tmp_csv.name

        # Handle rules
        if rules_file:
            with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp_rules:
                rules_content = await rules_file.read()
                tmp_rules.write(rules_content)
                rules_path = tmp_rules.name
        elif rules:
            rules_list = json.loads(rules)
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_rules:
                tmp_rules.write("\n".join(rules_list))
                rules_path = tmp_rules.name
        else:
            # No user rules - create empty rules file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_rules:
                tmp_rules.write("")
                rules_path = tmp_rules.name

        # Handle metadata (file takes precedence over text)
        metadata_content = ""
        if metadata_file:
            metadata_bytes = await metadata_file.read()
            metadata_content = metadata_bytes.decode("utf-8")
        elif metadata:
            metadata_content = metadata

        # Initialize state
        state = {
            "csv_path": csv_path,
            "rules_path": rules_path,
            "rules": [],
            "all_rules": [],
            "dataframe_json": "",
            "columns": [],
            "dtypes": {},
            "metadata": metadata_content,  # Column metadata for LLM
            "generated_code": "",
            "execution_results": [],
            "final_report": "",
            "errors": [],
        }

        # Load data
        result = load_data_node(state)
        state.update(result)

        # Generate AI rules
        result = rule_generator_node(state)
        state.update(result)

        # Store state
        thread_manager.set_state(thread_id, state)
        thread_manager.set_phase(thread_id, "rules_loaded")

        return RulesLoadedResponse(
            thread_id=thread_id,
            phase="rules_loaded",
            columns=state["columns"],
            dtypes=state["dtypes"],
            rules=[RuleModel(**r) for r in state["all_rules"]],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{thread_id}/rules")
async def update_rules(thread_id: str, request: RulesUpdateRequest):
    """Update the rules list (edit/delete operations from UI)."""
    thread = thread_manager.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    state = thread_manager.get_state(thread_id)
    if not state:
        raise HTTPException(status_code=400, detail="No state found for thread")

    # Update the rules in state
    state["all_rules"] = [r.model_dump() for r in request.rules]

    # Also update the flat rules list for code generation
    state["rules"] = [r.text for r in request.rules]

    thread_manager.set_state(thread_id, state)

    return {"message": "Rules updated", "count": len(request.rules)}


@router.post("/{thread_id}/confirm")
async def confirm_rules(thread_id: str):
    """Confirm rules and stream code generation + execution."""
    thread = thread_manager.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    phase = thread_manager.get_phase(thread_id)
    if phase != "rules_loaded":
        raise HTTPException(status_code=400, detail=f"Invalid phase: {phase}")

    state = thread_manager.get_state(thread_id)
    if not state:
        raise HTTPException(status_code=400, detail="No state found")

    # Update rules list from all_rules for code generation
    state["rules"] = [r["text"] for r in state.get("all_rules", [])]

    async def event_generator() -> AsyncGenerator[str, None]:
        nonlocal state

        try:
            # Generate Code
            thread_manager.set_phase(thread_id, "generating")
            yield f"event: status\ndata: {json.dumps({'step': 'code_generator', 'message': 'Generating validation code...'})}\n\n"
            await asyncio.sleep(0)

            result = code_generator_node(state)
            state.update(result)

            yield f"event: code_generated\ndata: {json.dumps({'generated_code': state['generated_code']})}\n\n"

            # Validate Code (AST + LLM review)
            thread_manager.set_phase(thread_id, "validating")
            yield f"event: status\ndata: {json.dumps({'step': 'code_validator', 'message': 'Validating generated code...'})}\n\n"
            await asyncio.sleep(0)

            result = code_validator_node(state)
            state.update(result)

            if not state.get("validation_passed", True):
                validation_details = state.get("validation_details", {})
                yield f"event: validation_failed\ndata: {json.dumps({'issues': validation_details})}\n\n"
                # Continue anyway but log the issues
            else:
                yield f"event: code_validated\ndata: {json.dumps({'message': 'Code validation passed'})}\n\n"

            # Execute Code
            thread_manager.set_phase(thread_id, "executing")
            yield f"event: status\ndata: {json.dumps({'step': 'code_executor', 'message': 'Executing validation code...'})}\n\n"
            await asyncio.sleep(0)

            result = code_executor_node(state)
            state.update(result)

            yield f"event: code_executed\ndata: {safe_json_dumps({'execution_results': state['execution_results']})}\n\n"

            # Format Results
            yield f"event: status\ndata: {json.dumps({'step': 'result_formatter', 'message': 'Formatting results...'})}\n\n"
            await asyncio.sleep(0)

            result = result_formatter_node(state)
            state.update(result)

            # Final response
            thread_manager.set_phase(thread_id, "complete")
            execution_results = state.get("execution_results", [])
            passed = sum(1 for r in execution_results if r.get("passed", False))
            failed = len(execution_results) - passed

            final_response = {
                "success": len(state.get("errors", [])) == 0,
                "summary": {"total_rules": len(execution_results), "passed": passed, "failed": failed},
                "results": execution_results,
                "generated_code": state.get("generated_code", ""),
                "final_report": state.get("final_report", ""),
                "errors": state.get("errors", []),
            }

            yield f"event: complete\ndata: {safe_json_dumps(final_response)}\n\n"
            thread_manager.set_state(thread_id, state)

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        finally:
            try:
                if state.get("csv_path"):
                    os.unlink(state["csv_path"])
                if state.get("rules_path"):
                    os.unlink(state["rules_path"])
            except Exception:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
