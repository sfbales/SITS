# endpoints/monitor.py
from fastapi import APIRouter, HTTPException
from models import SystemStatusResponse
import psutil

router = APIRouter()

@router.get("/system-status", response_model=SystemStatusResponse, summary="Get system resource usage", description="Retrieves the current CPU and memory usage information.")
def system_status():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        return {
            "cpu_usage": cpu_usage,
            "memory": {
                "total": memory_info.total,
                "used": memory_info.used,
                "free": memory_info.free,
                "percent": memory_info.percent,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

