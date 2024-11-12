# endpoints/filesystem.py
from fastapi import APIRouter, HTTPException
import os
import shutil
import logging
from pydantic import BaseModel
import datetime

router = APIRouter()
logger = logging.getLogger("uvicorn")

# Endpoint to create a new directory
@router.post("/create-directory")
async def create_directory(path: str):
    """Creates a new directory at the specified path."""
    try:
        logger.info(f"Attempting to create directory at path: {path}")
        if os.path.exists(path):
            logger.warning(f"Directory already exists: {path}")
            return {"message": f"Directory already exists at {path}"}
        
        os.makedirs(path, exist_ok=True)
        logger.info(f"Directory successfully created at: {path}")
        return {"message": f"Directory created at {path}"}
    except PermissionError as e:
        logger.error(f"Permission denied when creating directory at {path}: {e}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating directory at {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating directory: {str(e)}")

# Endpoint to delete a file or directory
@router.delete("/delete")
async def delete_file_or_directory(path: str):
    """Deletes a file or directory at the specified path."""
    if not os.path.exists(path):
        logger.warning(f"Delete failed - path not found: {path}")
        raise HTTPException(status_code=404, detail="Path not found")

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            logger.info(f"Directory deleted at path: {path}")
        else:
            os.remove(path)
            logger.info(f"File deleted at path: {path}")
        return {"message": f"Deleted {path}"}
    except PermissionError as e:
        logger.error(f"Permission denied when deleting path at {path}: {e}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error deleting path at {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting path: {str(e)}")

# Endpoint to list contents of a directory
@router.get("/list")
async def list_directory_contents(path: str):
    """Lists contents of the specified directory."""
    if not os.path.isdir(path):
        logger.warning(f"List contents failed - path is not a directory or does not exist: {path}")
        raise HTTPException(status_code=400, detail="Path is not a directory or does not exist")
    
    try:
        contents = os.listdir(path)
        logger.info(f"Listed contents of directory at path: {path}")
        return {"contents": contents}
    except PermissionError as e:
        logger.error(f"Permission denied when listing directory contents at {path}: {e}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error listing directory contents at {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing directory contents: {str(e)}")

# Endpoint to read a file
@router.get("/read-file")
async def read_file(path: str):
    """Reads contents of a specified file."""
    if not os.path.isfile(path):
        logger.warning(f"Read file failed - path is not a file or does not exist: {path}")
        raise HTTPException(status_code=400, detail="Path is not a file or does not exist")
    try:
        with open(path, 'r') as file:
            contents = file.read()
        logger.info(f"Read file at path: {path}")
        return {"contents": contents}
    except PermissionError as e:
        logger.error(f"Permission denied when reading file at {path}: {e}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error reading file at {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

# Model for write file request
class FileWriteRequest(BaseModel):
    path: str
    content: str

# Endpoint to write to a file
@router.post("/write-file")
async def write_file(request: FileWriteRequest):
    """Writes content to a specified file."""
    try:
        with open(request.path, 'w') as file:
            file.write(request.content)
        logger.info(f"Wrote to file at path: {request.path}")
        return {"message": f"File written at {request.path}"}
    except PermissionError as e:
        logger.error(f"Permission denied when writing file at {request.path}: {e}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error writing file at {request.path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")

# Endpoint to get metadata for a file or directory
@router.get("/metadata")
async def get_metadata(path: str):
    """Retrieves metadata for a file or directory."""
    if not os.path.exists(path):
        logger.warning(f"Metadata request failed - path does not exist: {path}")
        raise HTTPException(status_code=404, detail="Path does not exist")
    try:
        stats = os.stat(path)
        metadata = {
            "size": stats.st_size,
            "modified": datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "created": datetime.datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "is_directory": os.path.isdir(path),
        }
        logger.info(f"Retrieved metadata for path: {path}")
        return {"metadata": metadata}
    except PermissionError as e:
        logger.error(f"Permission denied when accessing metadata at {path}: {e}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error retrieving metadata at {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metadata: {str(e)}")

