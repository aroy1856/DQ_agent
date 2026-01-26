"""
FastAPI application for the DQ Agent.

Multi-turn conversation support with thread management and AI rule generation.
"""
import os
import json
import tempfile
import asyncio
import numpy as np
from typing import Optional, AsyncGenerator, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.dq_agent.nodes import (
    load_data_node,
    code_generator_node,
    code_executor_node,
    result_formatter_node,
    rule_generator_node,
)
from src.dq_agent.thread_manager import thread_manager


def convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def safe_json_dumps(obj: Any) -> str:
    """Safely serialize object to JSON, handling numpy types."""
    return json.dumps(convert_numpy_types(obj))


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set.")
    yield


app = FastAPI(
    title="DQ Agent API",
    description="Data Quality Agent with AI rule generation",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class ThreadResponse(BaseModel):
    thread_id: str
    phase: str
    message: str


class RuleModel(BaseModel):
    id: str
    text: str
    source: str  # "user" or "llm"


class RulesLoadedResponse(BaseModel):
    thread_id: str
    phase: str
    columns: list[str]
    dtypes: dict[str, str]
    rules: list[RuleModel]


class RulesUpdateRequest(BaseModel):
    rules: list[RuleModel]


@app.get("/")
async def root():
    return {"status": "healthy", "service": "DQ Agent API", "version": "2.1.0"}


@app.post("/thread/create", response_model=ThreadResponse)
async def create_thread():
    thread_id = thread_manager.create_thread()
    return ThreadResponse(
        thread_id=thread_id,
        phase="created",
        message="Thread created. Upload CSV and rules to continue.",
    )


@app.post("/thread/{thread_id}/load-rules", response_model=RulesLoadedResponse)
async def load_rules(
    thread_id: str,
    csv_file: UploadFile = File(...),
    rules_file: Optional[UploadFile] = File(None),
    rules: Optional[str] = Form(None),
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

        # Initialize state
        state = {
            "csv_path": csv_path,
            "rules_path": rules_path,
            "rules": [],
            "all_rules": [],
            "dataframe_json": "",
            "columns": [],
            "dtypes": {},
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


@app.put("/thread/{thread_id}/rules")
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


@app.post("/thread/{thread_id}/confirm")
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


@app.get("/thread/{thread_id}")
async def get_thread_status(thread_id: str):
    thread = thread_manager.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {
        "thread_id": thread_id,
        "phase": thread.get("phase"),
        "created_at": thread.get("created_at").isoformat(),
        "updated_at": thread.get("updated_at").isoformat(),
    }


@app.delete("/thread/{thread_id}")
async def delete_thread(thread_id: str):
    state = thread_manager.get_state(thread_id)
    if state:
        try:
            if state.get("csv_path"):
                os.unlink(state["csv_path"])
            if state.get("rules_path"):
                os.unlink(state["rules_path"])
        except Exception:
            pass
    
    if thread_manager.delete_thread(thread_id):
        return {"message": "Thread deleted"}
    raise HTTPException(status_code=404, detail="Thread not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
