import os
import json
import uuid
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from graph import run_workflow, stream_workflow
from metric_ai_wrapper import register_user, register_session
from providers import get_available_providers

app = FastAPI(title="Metric AI Agent Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MEMORY_DIR = Path(__file__).parent / "memory"


def load_json(filename: str):
    filepath = MEMORY_DIR / filename
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(filename: str, data):
    filepath = MEMORY_DIR / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    query: str
    provider: Optional[str] = "openai"
    model: Optional[str] = None


@app.post("/api/signup")
def signup(request: SignupRequest):
    users = load_json("users.json")

    existing = next((u for u in users if u["email"] == request.email), None)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    session_id = f"sess_{uuid.uuid4().hex[:8]}"

    new_user = {
        "user_id": user_id,
        "name": request.name,
        "email": request.email,
        "password": request.password,
        "role": "User",
    }
    users.append(new_user)
    save_json("users.json", users)

    sessions = load_json("sessions.json")
    sessions.append({"session_id": session_id, "user_id": user_id})
    save_json("sessions.json", sessions)

    register_user(user_id, request.name, "User")
    register_session(session_id, user_id)

    return {
        "user_id": user_id,
        "name": request.name,
        "role": "User",
        "session_id": session_id,
    }


@app.post("/api/login")
def login(request: LoginRequest):
    users = load_json("users.json")
    user = next(
        (u for u in users if u["email"] == request.email and u["password"] == request.password),
        None,
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = f"sess_{uuid.uuid4().hex[:8]}"

    sessions = load_json("sessions.json")
    sessions.append({"session_id": session_id, "user_id": user["user_id"]})
    save_json("sessions.json", sessions)

    register_user(user["user_id"], user["name"], user["role"])
    register_session(session_id, user["user_id"])

    providers = get_available_providers()

    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "role": user["role"],
        "session_id": session_id,
        "providers": providers,
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    result = run_workflow(
        user_id=request.user_id,
        session_id=request.session_id,
        query=request.query,
        provider=request.provider or "openai",
        model=request.model,
    )
    return result


@app.post("/api/stream")
async def chat_stream(request: ChatRequest):
    provider = request.provider or "openai"
    model = request.model

    def event_generator():
        start = time.time()
        trace_id = f"trc_{uuid.uuid4().hex[:8]}"

        agent_name, agent_id, token_gen = stream_workflow(
            user_id=request.user_id,
            session_id=request.session_id,
            query=request.query,
            provider=provider,
            model=model,
        )

        meta = json.dumps({
            "agent": agent_name,
            "agent_id": agent_id,
            "trace_id": trace_id,
            "provider": provider,
            "model": model or "gpt-4o-mini",
        })
        yield f"event: meta\ndata: {meta}\n\n"

        full_response = []
        for token in token_gen:
            full_response.append(token)
            data = json.dumps({"token": token})
            yield f"event: token\ndata: {data}\n\n"

        total_time = time.time() - start
        done_data = json.dumps({
            "execution_time": round(total_time, 2),
            "execution_time_ms": round(total_time * 1000),
        })
        yield f"event: done\ndata: {done_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/providers")
def list_providers():
    return get_available_providers()


@app.get("/api/traces")
def get_traces(user_id: str = None, session_id: str = None):
    traces = load_json("traces.json")
    if user_id:
        traces = [t for t in traces if t.get("user_id") == user_id]
    if session_id:
        traces = [t for t in traces if t.get("session_id") == session_id]
    return traces[-50:]


@app.get("/")
def root():
    return RedirectResponse(url="/login.html")


app.mount("/static", StaticFiles(directory=str(Path(__file__).parent.parent / "frontend")), name="static")
app.mount("/", StaticFiles(directory=str(Path(__file__).parent.parent / "frontend"), html=True), name="frontend")
