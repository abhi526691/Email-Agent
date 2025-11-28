import threading
import time
from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.main import run_polling_loop

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global Agent State
agent_thread = None
stop_event = None
agent_status = "Stopped"
last_run_time = "Never"

# --- Agent Control Endpoints ---

def run_agent_wrapper(event):
    global agent_status, last_run_time
    try:
        last_run_time = time.strftime("%Y-%m-%d %H:%M:%S")
        run_polling_loop(stop_event=event)
    except Exception as e:
        print(f"Agent thread error: {e}")
    finally:
        agent_status = "Stopped"

@app.post("/agent/start")
@limiter.limit("5/minute")
async def start_agent(request: Request):
    global agent_thread, stop_event, agent_status
    
    if agent_thread and agent_thread.is_alive():
        raise HTTPException(status_code=400, detail="Agent is already running")

    stop_event = threading.Event()
    agent_thread = threading.Thread(target=run_agent_wrapper, args=(stop_event,))
    agent_thread.start()
    agent_status = "Running"
    
    return {"status": "success", "message": "Agent started"}

@app.post("/agent/stop")
@limiter.limit("5/minute")
async def stop_agent(request: Request):
    global stop_event, agent_status
    
    if not agent_thread or not agent_thread.is_alive():
        raise HTTPException(status_code=400, detail="Agent is not running")

    if stop_event:
        stop_event.set()
    
    agent_status = "Stopping..."
    return {"status": "success", "message": "Agent stopping..."}

@app.get("/agent/status")
async def get_status():
    global agent_status, last_run_time
    
    # Update status if thread finished naturally
    if agent_thread and not agent_thread.is_alive() and agent_status == "Running":
        agent_status = "Stopped"

    return {
        "status": agent_status,
        "last_run": last_run_time
    }
