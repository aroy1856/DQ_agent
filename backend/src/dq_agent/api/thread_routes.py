"""
Thread management routes for the DQ Agent API.
"""
import os

from fastapi import APIRouter, HTTPException

from src.dq_agent.thread_manager import thread_manager
from src.dq_agent.api.models import ThreadResponse


router = APIRouter()


@router.post("/create", response_model=ThreadResponse)
async def create_thread():
    thread_id = thread_manager.create_thread()
    return ThreadResponse(
        thread_id=thread_id,
        phase="created",
        message="Thread created. Upload CSV and rules to continue.",
    )


@router.get("/{thread_id}")
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


@router.delete("/{thread_id}")
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
