"""
Pydantic request/response models for the DQ Agent API.
"""
from pydantic import BaseModel


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
