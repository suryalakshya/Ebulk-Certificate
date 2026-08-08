import subprocess
import time
import sys
import os

print("=" * 70)
print("STARTING CERTIFICATE GENERATOR & EMAIL DISPATCHER")
print("=" * 70)

# Start FastAPI backend
backend_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
print("Starting Python FastAPI backend on http://127.0.0.1:8000 ...")
backend_proc = subprocess.Popen(backend_cmd, cwd=os.path.join(os.path.dirname(__file__), "backend"))

time.sleep(2)

# Start Vite frontend dev server
frontend_cmd = ["npm.cmd" if os.name == "nt" else "npm", "run", "dev"]
print("Starting React Frontend on http://localhost:3000 ...")
frontend_proc = subprocess.Popen(frontend_cmd, cwd=os.path.join(os.path.dirname(__file__), "frontend"))

print("\n✓ Both servers are active!")
print("  - Backend API: http://127.0.0.1:8000")
print("  - Frontend UI:  http://localhost:3000")
print("\nPress Ctrl+C to stop both servers.\n")

try:
    backend_proc.wait()
    frontend_proc.wait()
except KeyboardInterrupt:
    print("\nStopping servers...")
    backend_proc.terminate()
    frontend_proc.terminate()
    print("Done.")
