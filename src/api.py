import asyncio
from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from src.agent_controller import start_agent, stop_agent, get_agent_status
from src.telegram_bot import get_bot_handler

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and start Telegram bot
    bot_handler = get_bot_handler()
    await bot_handler.start_bot()
    print("✅ FastAPI server and Telegram bot are running")
    
    yield
    
    # Shutdown: Stop Telegram bot
    await bot_handler.stop_bot()
    print("🛑 FastAPI server and Telegram bot stopped")

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Agent Control Endpoints ---

@app.post("/agent/start")
@limiter.limit("5/minute")
async def start_agent_endpoint(request: Request):
    result = start_agent()
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {"status": "success", "message": result["message"]}

@app.post("/agent/stop")
@limiter.limit("5/minute")
async def stop_agent_endpoint(request: Request):
    result = stop_agent()
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {"status": "success", "message": result["message"]}

@app.get("/agent/status")
async def get_status_endpoint():
    status_info = get_agent_status()
    return status_info
