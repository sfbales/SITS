# endpoints/modules.py
from fastapi import APIRouter, HTTPException
from models import ModuleRequest, ModuleListResponse
from utils.sits_integration import create_sits_module, list_modules

router = APIRouter()

@router.post("/create", summary="Create a new SITS module", description="Creates a new module with a specified name and description.")
def create_module(request: ModuleRequest):
    try:
        create_sits_module(request.name, request.description)
        return {"message": f"Module '{request.name}' created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=ModuleListResponse, summary="List all SITS modules", description="Lists all modules currently available in the SITS environment.")
def list_all_modules():
    try:
        modules = list_modules()
        return {"modules": modules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

