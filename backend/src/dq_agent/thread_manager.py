"""
Thread management for multi-turn DQ conversations.
"""
import uuid
from typing import Any
from datetime import datetime, timedelta
from threading import Lock


class ThreadManager:
    """Manages conversation threads with state persistence."""
    
    def __init__(self, expiry_minutes: int = 30):
        self._threads: dict[str, dict[str, Any]] = {}
        self._lock = Lock()
        self._expiry_delta = timedelta(minutes=expiry_minutes)
    
    def create_thread(self) -> str:
        """Create a new thread and return its ID."""
        thread_id = str(uuid.uuid4())
        with self._lock:
            self._threads[thread_id] = {
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "state": {},
                "phase": "created",  # created, rules_loaded, confirmed, generating, executing, complete
            }
        return thread_id
    
    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        """Get thread by ID, returns None if not found or expired."""
        with self._lock:
            thread = self._threads.get(thread_id)
            if thread is None:
                return None
            
            # Check expiry
            if datetime.now() - thread["updated_at"] > self._expiry_delta:
                del self._threads[thread_id]
                return None
            
            return thread
    
    def update_thread(self, thread_id: str, updates: dict[str, Any]) -> bool:
        """Update thread state. Returns False if thread not found."""
        with self._lock:
            if thread_id not in self._threads:
                return False
            
            self._threads[thread_id].update(updates)
            self._threads[thread_id]["updated_at"] = datetime.now()
            return True
    
    def set_state(self, thread_id: str, state: dict[str, Any]) -> bool:
        """Set the DQ state for a thread."""
        with self._lock:
            if thread_id not in self._threads:
                return False
            
            self._threads[thread_id]["state"] = state
            self._threads[thread_id]["updated_at"] = datetime.now()
            return True
    
    def get_state(self, thread_id: str) -> dict[str, Any] | None:
        """Get the DQ state for a thread."""
        thread = self.get_thread(thread_id)
        if thread is None:
            return None
        return thread.get("state", {})
    
    def set_phase(self, thread_id: str, phase: str) -> bool:
        """Update the phase of a thread."""
        return self.update_thread(thread_id, {"phase": phase})
    
    def get_phase(self, thread_id: str) -> str | None:
        """Get the current phase of a thread."""
        thread = self.get_thread(thread_id)
        if thread is None:
            return None
        return thread.get("phase")
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread."""
        with self._lock:
            if thread_id in self._threads:
                del self._threads[thread_id]
                return True
            return False
    
    def cleanup_expired(self) -> int:
        """Remove expired threads. Returns count of removed threads."""
        now = datetime.now()
        removed = 0
        with self._lock:
            expired = [
                tid for tid, t in self._threads.items()
                if now - t["updated_at"] > self._expiry_delta
            ]
            for tid in expired:
                del self._threads[tid]
                removed += 1
        return removed


# Global thread manager instance
thread_manager = ThreadManager()
