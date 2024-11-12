# endpoints/network.py
from fastapi import APIRouter, HTTPException
import subprocess
import psutil

router = APIRouter()

@router.get("/configuration")
async def network_configuration():
    """Retrieves the current network configuration details."""
    try:
        net_info = {
            iface: [addr.address for addr in addrs if addr.family == 2]  # Family 2 represents IPv4 addresses
            for iface, addrs in psutil.net_if_addrs().items()
        }
        return {"network_config": net_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving network configuration: {str(e)}")

@router.post("/ping")
async def ping_host(host: str):
    """Pings a given host and returns the result."""
    try:
        result = subprocess.run(["ping", "-c", "4", host], capture_output=True, text=True)
        return {"output": result.stdout, "error": result.stderr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pinging host: {str(e)}")

