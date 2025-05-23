from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Vibration Game Backend",
    description="API for the Vibration web game with personalized AI agents.",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Vibration Game API"}

# Placeholder for future startup events, e.g., DB connection
@app.on_event("startup")
async def startup_event():
    print("Application startup")
    # Example: await database.connect()

# Placeholder for future shutdown events
@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown")
    # Example: await database.disconnect()

# Further routers will be included here
# from .api.endpoints import some_router
# app.include_router(some_router, prefix="/api/v1")
