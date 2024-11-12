# main.py
import logging
from fastapi import FastAPI
from endpoints import commands, filesystem, network, processes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize the app
app = FastAPI(title="SITS API")

# Include routes
app.include_router(commands.router, prefix="/commands", tags=["Commands"])
app.include_router(filesystem.router, prefix="/filesystem", tags=["Filesystem"])
app.include_router(network.router, prefix="/network", tags=["Network"])
app.include_router(processes.router, prefix="/processes", tags=["Processes"])

# Root and health check endpoints
@app.get("/")
def read_root():
    logging.info("Root endpoint accessed")
    return {"message": "Welcome to the SITS API!"}

@app.get("/health")
def health_check():
    logging.info("Health check endpoint accessed")
    return {"status": "healthy"}

