# models.py
from pydantic import BaseModel

class CommandRequest(BaseModel):
    command: str

class CommandResponse(BaseModel):
    output: str
    error: str

class ModuleRequest(BaseModel):
    name: str
    description: str

class ModuleListResponse(BaseModel):
    modules: list[str]

class SystemStatusResponse(BaseModel):
    cpu_usage: float
    memory: dict

