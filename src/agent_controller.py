"""
Shared agent controller for managing the email agent state.
This module is used by both the FastAPI API and Telegram bot.
"""
import threading
import time
from src.main import run_polling_loop

# Global Agent State
agent_thread = None
stop_event = None
agent_status = "Stopped"
last_run_time = "Never"

def start_agent():
    """Start the email agent in a background thread"""
    global agent_thread, stop_event, agent_status, last_run_time
    
    if agent_thread and agent_thread.is_alive():
        return {"success": False, "message": "Agent is already running"}
    
    stop_event = threading.Event()
    agent_thread = threading.Thread(target=_run_agent_wrapper, args=(stop_event,))
    agent_thread.start()
    agent_status = "Running"
    
    return {"success": True, "message": "Agent started successfully"}

def stop_agent():
    """Stop the email agent"""
    global stop_event, agent_status
    
    if not agent_thread or not agent_thread.is_alive():
        return {"success": False, "message": "Agent is not running"}
    
    if stop_event:
        stop_event.set()
    
    agent_status = "Stopping..."
    return {"success": True, "message": "Agent stopping..."}

def get_agent_status():
    """Get the current agent status"""
    global agent_status, last_run_time, agent_thread
    
    # Update status if thread finished naturally
    if agent_thread and not agent_thread.is_alive() and agent_status == "Running":
        agent_status = "Stopped"
    
    return {
        "status": agent_status,
        "last_run": last_run_time
    }

def _run_agent_wrapper(event):
    """Wrapper function to run the agent with error handling"""
    global agent_status, last_run_time
    try:
        last_run_time = time.strftime("%Y-%m-%d %H:%M:%S")
        run_polling_loop(stop_event=event)
    except Exception as e:
        print(f"Agent thread error: {e}")
    finally:
        agent_status = "Stopped"
