"""
Ashiee Application Server
FastAPI web server serving the constructed login portal, dashboard, and REST API.
"""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

import auth

app = FastAPI(title="Ashiee Constructed Web Portal")
BASE_DIR = Path(__file__).parent.resolve()

class AuthPayload(BaseModel):
    username: str
    password: str

@app.get("/")
async def serve_root():
    for f in ["active_app.html", "calculator.html", "todo.html", "snake.html", "weather.html", "portfolio.html", "login.html"]:
        p = BASE_DIR / f
        if p.exists():
            return FileResponse(p)
    return {"status": "ok", "service": "Ashiee Constructed Application Server"}

@app.get("/login")
async def serve_login():
    return FileResponse(BASE_DIR / "login.html")

@app.get("/calculator")
async def serve_calc():
    if (BASE_DIR / "calculator.html").exists():
        return FileResponse(BASE_DIR / "calculator.html")
    return FileResponse(BASE_DIR / "login.html")

@app.get("/todo")
async def serve_todo():
    if (BASE_DIR / "todo.html").exists():
        return FileResponse(BASE_DIR / "todo.html")
    return FileResponse(BASE_DIR / "login.html")

@app.get("/snake")
async def serve_snake():
    if (BASE_DIR / "snake.html").exists():
        return FileResponse(BASE_DIR / "snake.html")
    return FileResponse(BASE_DIR / "login.html")

@app.get("/weather")
async def serve_weather():
    if (BASE_DIR / "weather.html").exists():
        return FileResponse(BASE_DIR / "weather.html")
    return FileResponse(BASE_DIR / "login.html")

@app.get("/portfolio")
async def serve_portfolio():
    if (BASE_DIR / "portfolio.html").exists():
        return FileResponse(BASE_DIR / "portfolio.html")
    return FileResponse(BASE_DIR / "login.html")

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(BASE_DIR / "dashboard.html")

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Ashiee Login System", "port": 5000}

@app.post("/api/register")
async def register(payload: AuthPayload):
    ok = auth.register_user(payload.username, payload.password)
    if not ok:
        raise HTTPException(status_code=400, detail="Username already exists or password is too short (min 4 chars).")
    return {"success": True, "message": "User registered successfully!"}

@app.post("/api/login")
async def login(payload: AuthPayload):
    ok = auth.verify_login(payload.username, payload.password)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = auth.create_session(payload.username)
    return {"success": True, "token": token, "username": payload.username}

@app.get("/api/me")
async def me(request: Request):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    session = auth.verify_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return {"success": True, "user": session}

@app.post("/api/logout")
async def logout(request: Request):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    auth.revoke_session(token)
    return {"success": True, "message": "Logged out."}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
