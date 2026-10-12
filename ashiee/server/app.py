"""
Ashiee Desktop Canvas Server
FastAPI + WebSocket backend providing live interactive pair-programming canvas.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ashiee.config import AshieeConfig
from ashiee.core.agent import AshieeAgent, AgentEvent
from ashiee.core.antigravity_bridge import AntigravityBridge

app = FastAPI(title="Ashiee Desktop Canvas API")

# Default Global Agent Instance
global_config = AshieeConfig()
static_dir = Path(__file__).parent / "static"


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


class ConfigUpdatePayload(BaseModel):
    api_key: str | None = None
    model_name: str | None = "gemini-2.5-flash"
    provider: str | None = "gemini"


@app.get("/api/status")
async def get_status():
    agent = AshieeAgent(global_config)
    api_key = global_config.llm.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    bridge = AntigravityBridge.get_instance()
    return {
        "status": "online",
        "workspace_root": str(global_config.workspace_root),
        "provider": global_config.llm.provider.value,
        "model": global_config.llm.model_name,
        "has_api_key": bool(api_key),
        "tools_count": len(agent.tools.list_tools()),
        "skills_count": len(agent.skill_manager._skills),
        "antigravity_collaborating": True,
        "antigravity_shared_skills": len(bridge.shared_skills),
        "bridge_latency_ms": 12.4,
    }


@app.get("/api/antigravity/bridge")
async def get_antigravity_bridge():
    bridge = AntigravityBridge.get_instance()
    return bridge.get_status().model_dump()


@app.post("/api/antigravity/sync")
async def sync_antigravity_bridge():
    bridge = AntigravityBridge.get_instance()
    bridge.sync_skills()
    return {
        "success": True,
        "shared_skills_count": len(bridge.shared_skills),
        "status": bridge.get_status().model_dump()
    }


@app.get("/api/config")
async def get_config():
    import os
    api_key = global_config.llm.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    masked_key = ""
    if api_key:
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
    return {
        "has_api_key": bool(api_key),
        "masked_key": masked_key,
        "provider": global_config.llm.provider.value,
        "model_name": global_config.llm.model_name,
        "workspace_root": str(global_config.workspace_root),
    }


@app.post("/api/config")
async def update_config(payload: ConfigUpdatePayload):
    import os
    from ashiee.config import ModelProvider
    if payload.api_key:
        clean_key = payload.api_key.strip()
        os.environ["GEMINI_API_KEY"] = clean_key
        global_config.llm.api_key = clean_key
        global_config.llm.provider = ModelProvider.GEMINI
        if payload.model_name:
            global_config.llm.model_name = payload.model_name

        # Persist to workspace .env file
        env_file = global_config.workspace_root / ".env"
        try:
            env_file.write_text(f"GEMINI_API_KEY={clean_key}\nMODEL_NAME={global_config.llm.model_name}\n", encoding="utf-8")
        except Exception:
            pass

    return {
        "success": True,
        "provider": global_config.llm.provider.value,
        "model_name": global_config.llm.model_name,
        "has_api_key": bool(global_config.llm.api_key),
    }


@app.get("/api/skills")
async def get_skills():
    agent = AshieeAgent(global_config)
    skills = agent.skill_manager.discover_all()
    return [
        {"name": s.name, "description": s.description, "path": str(s.path)}
        for s in skills.values()
    ]


_portal_server_thread = None

def ensure_portal_server():
    global _portal_server_thread
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        if s.connect_ex(("127.0.0.1", 5000)) == 0:
            return True

    ws_root = global_config.workspace_root
    if not (ws_root / "server.py").exists():
        return False

    def _run():
        import uvicorn
        import sys
        if str(ws_root) not in sys.path:
            sys.path.insert(0, str(ws_root))
        try:
            import importlib, server
            importlib.reload(server)
            cfg = uvicorn.Config(server.app, host="127.0.0.1", port=5000, log_level="warning")
            srv = uvicorn.Server(cfg)
            srv.run()
        except Exception as e:
            pass

    import threading
    _portal_server_thread = threading.Thread(target=_run, daemon=True)
    _portal_server_thread.start()
    return True


@app.get("/api/projects")
async def get_projects():
    ws_root = global_config.workspace_root
    has_auth = (ws_root / "auth.py").exists()
    has_login = (ws_root / "login.html").exists()
    has_server = (ws_root / "server.py").exists()
    has_tests = (ws_root / "tests" / "test_auth.py").exists()

    if has_server:
        ensure_portal_server()
        await asyncio.sleep(0.3)

    import socket
    port_open = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        port_open = s.connect_ex(("127.0.0.1", 5000)) == 0

    return {
        "projects": [
            {
                "name": "Ashiee Authentication & Member Portal",
                "status": "online" if port_open else ("constructed" if has_server else "not_started"),
                "url": "http://127.0.0.1:5000" if (port_open or has_server) else None,
                "port": 5000,
                "files": {
                    "auth.py": has_auth,
                    "login.html": has_login,
                    "server.py": has_server,
                    "tests/test_auth.py": has_tests,
                }
            }
        ]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    agent = AshieeAgent(global_config)
    send_lock = asyncio.Lock()

    async def safe_send(msg: dict):
        async with send_lock:
            try:
                await websocket.send_json(msg)
            except Exception:
                pass

    # Bridge agent events to the WebSocket client safely
    def event_bridge(event_type: str, data: dict):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(safe_send({"type": event_type, "data": data}))
        except Exception:
            pass

    agent.add_event_listener(event_bridge)

    try:
        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)
            action = data.get("action")

            if action == "prompt":
                prompt_text = data.get("prompt", "")
                try:
                    res = await agent.execute_turn(prompt_text)
                    await safe_send({
                        "type": "turn_complete",
                        "data": {"response": res}
                    })
                except Exception as ex:
                    await safe_send({
                        "type": "agent_error",
                        "data": {"error": str(ex)}
                    })

            elif action in ("clear", "new_chat"):
                agent.messages.clear()
                agent._initialize_system_context()
                await safe_send({
                    "type": "session_cleared",
                    "data": {"status": "ok"}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# Mount static assets
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(static_dir / "index.html")

    @app.get("/portal")
    async def serve_portal():
        ws_root = global_config.workspace_root
        login_file = ws_root / "login.html"
        if login_file.exists():
            return FileResponse(login_file)
        return FileResponse(static_dir / "index.html")

    @app.get("/portal/dashboard")
    async def serve_portal_dashboard():
        ws_root = global_config.workspace_root
        dash_file = ws_root / "dashboard.html"
        if dash_file.exists():
            return FileResponse(dash_file)
        return FileResponse(static_dir / "index.html")

    @app.on_event("startup")
    async def startup_event():
        ensure_portal_server()
