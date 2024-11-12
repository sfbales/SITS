# utils/sits_integration.py
import subprocess
import os

def execute_shell_command(command: str):
    """Executes a shell command and returns the output and error."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode().strip(), stderr.decode().strip()

