import random
import socket
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Literal, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Agent Registry", version="1.0.0")

# ── State ──────────────────────────────────────────────────────────────────────
# agents[agent_id] = {ip, port, platform, tags, load, last_seen, registered_at}
agents: Dict[str, dict] = {}
_lock = threading.Lock()
_rr_index = 0

HEARTBEAT_TIMEOUT = 30  # seconds


# ── Helpers ────────────────────────────────────────────────────────────────────

def _live_agents(tag: Optional[str] = None) -> Dict[str, dict]:
    now = time.time()
    with _lock:
        return {
            k: v
            for k, v in agents.items()
            if now - v["last_seen"] <= HEARTBEAT_TIMEOUT
            and (tag is None or tag in v.get("tags", []))
        }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.post("/register")
def register(
    agent_id: str,
    ip: str,
    port: int,
    platform: str = "unknown",
    tags: str = "",
    load: int = 0,
):
    """Register an agent. Re-registering updates all fields."""
    with _lock:
        agents[agent_id] = {
            "ip": ip,
            "port": port,
            "platform": platform,
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "load": load,
            "last_seen": time.time(),
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
    print(f"[register] {agent_id} @ {ip}:{port}  tags={tags}")
    return {"status": "ok", "agent_id": agent_id}


@app.post("/heartbeat")
def heartbeat(agent_id: str, load: int = 0):
    """Update heartbeat timestamp and optionally report current task load."""
    with _lock:
        if agent_id not in agents:
            raise HTTPException(status_code=404, detail="Agent not registered")
        agents[agent_id]["last_seen"] = time.time()
        agents[agent_id]["load"] = load
    return {"status": "ok"}


@app.get("/agents")
def get_agents(tag: Optional[str] = Query(default=None)):
    """List all live agents, optionally filtered by tag."""
    return _live_agents(tag)


@app.get("/pick")
def pick_agent(
    strategy: Literal["random", "round_robin", "least_load"] = Query(default="round_robin"),
    tag: Optional[str] = Query(default=None),
):
    global _rr_index
    live = _live_agents(tag)
    if not live:
        raise HTTPException(status_code=503, detail="No available agents")

    keys = list(live.keys())

    if strategy == "random":
        chosen = random.choice(keys)
    elif strategy == "least_load":
        chosen = min(keys, key=lambda k: live[k]["load"])
    else:  # round_robin
        with _lock:
            chosen = keys[_rr_index % len(keys)]
            _rr_index += 1

    return {"agent_id": chosen, **live[chosen]}


@app.get("/health")
def health():
    with _lock:
        total = len(agents)
    live = len(_live_agents())
    return {"status": "ok", "agents_total": total, "agents_live": live}


# ── Background: expire stale agents ───────────────────────────────────────────

def _expire_loop():
    while True:
        time.sleep(HEARTBEAT_TIMEOUT)
        now = time.time()
        with _lock:
            stale = [k for k, v in agents.items() if now - v["last_seen"] > HEARTBEAT_TIMEOUT]
            for k in stale:
                print(f"[expire] stale agent removed: {k}")
                del agents[k]


threading.Thread(target=_expire_loop, daemon=True).start()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    port = int(os.getenv("REGISTRY_PORT", 8001))
    print(f"Registry running at http://{socket.gethostname()}:{port}")
    uvicorn.run(app, host="::", port=port)
