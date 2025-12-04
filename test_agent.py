"""
Test script to debug agent start/stop behavior
"""
import time
from src.agent_controller import start_agent, get_agent_status

print("=" * 50)
print("Testing Agent Start with Backfill Mode")
print("=" * 50)

# Start agent
result = start_agent(mode="backfill")
print(f"\nStart result: {result}")

# Monitor status
for i in range(20):  # Check for 20 seconds
    time.sleep(1)
    status = get_agent_status()
    print(f"[{i+1}s] Status: {status['status']}, Last Run: {status['last_run']}")
    
    if status['status'] == 'Stopped':
        print("\n⚠️ Agent stopped unexpectedly!")
        break

print("\n" + "=" * 50)
