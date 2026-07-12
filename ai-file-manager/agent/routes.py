# agent/routes.py
from fastapi import APIRouter
from pydantic import BaseModel
from executor import execute

router = APIRouter(prefix="/agent")

class ExecuteRequest(BaseModel):
    query: str
    auto_confirm: bool = False
    choice_index: int | None = None

@router.post("/execute")
def agent_execute(req: ExecuteRequest):
    return execute(req.query, auto_confirm=req.auto_confirm, choice_index=req.choice_index)