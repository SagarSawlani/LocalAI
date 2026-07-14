# agent/routes.py
from fastapi import APIRouter
from pydantic import BaseModel
from executor import execute, execute_plan

router = APIRouter(prefix="/agent")

class ExecuteRequest(BaseModel):
    query: str
    auto_confirm: bool = False
    choice_index: int | None = None

class ExecutePlanRequest(BaseModel):
    plan: dict

@router.post("/execute")
def agent_execute(req: ExecuteRequest):
    return execute(req.query, auto_confirm=req.auto_confirm, choice_index=req.choice_index)

@router.post("/execute-plan")
def agent_execute_plan(req: ExecutePlanRequest):
    return execute_plan(req.plan)