# endpoints/processes.py
from fastapi import APIRouter, HTTPException
import psutil

router = APIRouter()

@router.get("/list")
async def list_processes():
    """Lists active processes with details like PID, CPU, and memory usage."""
    try:
        processes = [
            {
                "pid": proc.pid,
                "name": proc.info["name"],
                "cpu_percent": proc.info["cpu_percent"],
                "memory_percent": proc.info["memory_percent"]
            }
            for proc in psutil.process_iter(["name", "cpu_percent", "memory_percent"])
        ]
        return {"processes": processes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing processes: {str(e)}")

@router.post("/kill")
async def kill_process(pid: int):
    """Terminates a process by PID."""
    try:
        process = psutil.Process(pid)
        process.terminate()
        return {"message": f"Process {pid} terminated"}
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail="Process not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error terminating process: {str(e)}")

