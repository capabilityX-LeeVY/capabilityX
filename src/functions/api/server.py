"""
FastAPI server configuration and setup
"""
import os
import sys
import threading
import time
import socket
import requests
from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)
        
import platform as platform_module
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rs_sdk.utils.event_listener import FocusListener
from rs_sdk.utils.control_recorder import ControlRecorder

# Platform-specific import for event listener
if platform_module.system() == "Windows":
    from rs_sdk.utils.event_listener import FocusListener
elif platform_module.system() == "Linux":
    from rs_sdk.platform.linux import FocusListener
else:
    # Default fallback for unsupported platforms
    from rs_sdk.utils.event_listener import FocusListener
from common.startup.startup_initializer import StartupInitializer

# Registry configuration — comma-separated REGISTRY_URLS for high availability
REGISTRIES = [
    url.strip()
    for url in os.getenv("REGISTRY_URLS", "http://localhost:8001").split(",")
    if url.strip()
]
AGENT_PORT = int(os.getenv("AGENT_PORT", 9909))


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def safe_request(url: str, params: dict):
    while True:
        try:
            requests.post(url, params=params, timeout=3)
            return
        except Exception as e:
            print(f"Retrying {url} in 5s: {e}")
            time.sleep(5)


def _broadcast(path: str, params: dict, persistent: bool = False):
    for registry in REGISTRIES:
        if persistent:
            threading.Thread(
                target=safe_request,
                args=(f"{registry}{path}", params),
                daemon=True,
            ).start()
        else:
            try:
                requests.post(f"{registry}{path}", params=params, timeout=3)
            except Exception as e:
                print(f"Request to {registry}{path} failed: {e}")


def register_agent():
    tags = os.getenv("AGENT_TAGS", f"{platform_module.system().lower()},accessibility")
    _broadcast(
        "/register",
        {
            "agent_id": socket.gethostname(),
            "ip": get_local_ip(),
            "port": AGENT_PORT,
            "platform": platform_module.system(),
            "tags": tags,
        },
        persistent=True,
    )


def heartbeat_loop():
    while True:
        _broadcast("/heartbeat", {"agent_id": socket.gethostname()})
        time.sleep(10)

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Webex RegressShield API",
        description="API for Webex accessibility testing and automation",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )
    
    # Initialize focus listener
    listener = FocusListener()
    listener.start()

    # Register to registry and start heartbeat
    register_agent()
    threading.Thread(target=heartbeat_loop, daemon=True).start()

    # Initialize control recorder
    # control_recorder = ControlRecorder()
    # control_recorder.reset_image_directory()

    # Import and include routes
    from functions.api.routes import router
    app.include_router(router, prefix="/api")

    @app.get("/info")
    def info():
        return {
            "agent_id": socket.gethostname(),
            "ip": get_local_ip(),
            "port": AGENT_PORT,
            "platform": platform_module.system(),
            "tags": ["windows", "accessibility"],
        }

    return app

def startup_initializer():
    StartupInitializer()

# Exit code that tells the wrapper script to restart
RESTART_EXIT_CODE = 42

def request_restart(delay: float = 1.0):
    """Schedule a graceful server restart after a short delay."""
    import threading
    def _shutdown():
        time.sleep(delay)
        print(f"=== Restarting server (exit {RESTART_EXIT_CODE}) ===")
        os._exit(RESTART_EXIT_CODE)
    threading.Thread(target=_shutdown, daemon=True).start()

# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    print(f"http://{socket.gethostname()}:{AGENT_PORT}")
    startup_initializer()
    uvicorn.run(app, host="::", port=AGENT_PORT)
