# commands.py
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from typing import List
import asyncio
import shlex
import subprocess

# Initialize router
router = APIRouter()
logger = logging.getLogger("uvicorn")

# Constants
MAX_HISTORY = 100  # Maximum number of commands to store in history

# Models for request and response
class CommandRequest(BaseModel):
    command: str = Field(..., example="ls -la /home/user")

    @validator('command')
    def validate_command(cls, v):
        if not v.strip():
            raise ValueError("Command cannot be empty.")
        # Add more validation rules as needed
        return v

class CommandResponse(BaseModel):
    output: str = Field(..., description="Standard output from the command.")
    error: str = Field(..., description="Error output from the command.")

class CommandHistoryResponse(BaseModel):
    history: List[str] = Field(..., description="List of previously executed commands.")

# Dependency for command history storage
class CommandHistory:
    def __init__(self, max_size: int = MAX_HISTORY):
        self.history: List[str] = []
        self.lock = asyncio.Lock()
        self.max_size = max_size

    async def add_command(self, command: str):
        async with self.lock:
            self.history.append(command)
            if len(self.history) > self.max_size:
                self.history.pop(0)

    async def get_history(self) -> List[str]:
        async with self.lock:
            return list(self.history)

async def get_command_history():
    return command_history_instance

# Initialize command history
command_history_instance = CommandHistory()

@router.post(
    "/execute",
    response_model=CommandResponse,
    summary="Execute a shell command",
    description="Executes a shell command based on the provided command string.",
)
async def execute_command(
    request: CommandRequest,
    history: CommandHistory = Depends(get_command_history)
) -> CommandResponse:
    command = request.command
    logger.info(f"Received command execution request: {command}")

    # Add to history
    await history.add_command(command)

    try:
        # Parse command safely
        args = shlex.split(command)
        logger.debug(f"Executing command with arguments: {args}")

        # Execute command asynchronously
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        # Decode outputs
        stdout_decoded = stdout.decode().strip()
        stderr_decoded = stderr.decode().strip()

        # Log outputs
        if stdout_decoded:
            logger.info(f"Command Output: {stdout_decoded}")
        if stderr_decoded:
            logger.warning(f"Command Error Output: {stderr_decoded}")

        return CommandResponse(output=stdout_decoded, error=stderr_decoded)

    except FileNotFoundError:
        logger.error(f"Command not found: {command}")
        raise HTTPException(status_code=400, detail="Command not found.")
    except Exception as e:
        logger.exception(f"Failed to execute command '{command}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

@router.get(
    "/history",
    response_model=CommandHistoryResponse,
    summary="Get Command History",
    description="Retrieves a list of previously executed commands.",
)
async def get_command_history_endpoint(
    history: CommandHistory = Depends(get_command_history)
) -> CommandHistoryResponse:
    logger.info("Fetching command history")
    history_list = await history.get_history()
    return CommandHistoryResponse(history=history_list)

