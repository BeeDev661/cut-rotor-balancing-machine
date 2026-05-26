import asyncio
import json
import os
import time
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional

import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from passlib.context import CryptContext
import logging

from backend.simulator import Simulator
from backend.mqtt_handler import MQTTHandler, mqtt_data_aggregator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()
sim = Simulator()

clients: List[WebSocket] = []

# ============ MQTT Configuration ============
USE_MQTT = os.getenv("USE_MQTT", "false").lower() == "true"
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "false").lower() == "true"

mqtt_handler: Optional[MQTTHandler] = None
mqtt_latest_data: Optional[dict] = None

# ============ Authentication & DB ============
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
SECRET_KEY = os.environ.get("DASHBOARD_SECRET", "change_this_secret_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db_conn():
    # allow short timeout and allow connections across threads
    conn = sqlite3.connect(DB_PATH, timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[sqlite3.Row]:
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        return row
    finally:
        conn.close()


def create_user(username: str, password: str):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        now = time.time()
        cur.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, get_password_hash(password), now),
        )
        conn.commit()
    finally:
        conn.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # use integer timestamp for exp to avoid JSON serialization issues
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def broadcaster():
    """
    Broadcasts sensor data to all connected WebSocket clients.
    Uses MQTT data if available, otherwise falls back to simulator.
    """
    while True:
        try:
            data_to_send = None
            
            # Priority: MQTT data if connected
            if USE_MQTT and mqtt_handler and mqtt_handler.is_connected() and mqtt_latest_data:
                if mqtt_latest_data.get("acc"):
                    data_to_send = json.dumps(mqtt_latest_data)
                    
            # Fallback: Simulator data
            if not data_to_send and sim.running and clients:
                msg = await sim.stream_chunk(duration=0.1)
                data_to_send = msg
            
            # Send to all connected clients
            if data_to_send and clients:
                remove = []
                for ws in clients:
                    try:
                        await ws.send_text(data_to_send)
                    except Exception:
                        remove.append(ws)
                for r in remove:
                    if r in clients:
                        clients.remove(r)
                        
        except Exception as e:
            logger.error(f"Broadcaster error: {e}")
            
        await asyncio.sleep(0.01)


@app.on_event("startup")
async def startup_event():
    global mqtt_handler, mqtt_latest_data
    
    init_db()
    
    # Initialize MQTT if enabled
    if USE_MQTT:
        try:
            mqtt_handler = MQTTHandler(
                broker_address=MQTT_BROKER,
                broker_port=MQTT_PORT,
                username=MQTT_USER if MQTT_USER else None,
                password=MQTT_PASSWORD if MQTT_PASSWORD else None,
                use_tls=MQTT_USE_TLS,
                client_id="dashboard_backend"
            )
            
            mqtt_latest_data = await mqtt_data_aggregator(mqtt_handler)
            
            if mqtt_handler.connect():
                logger.info(f"MQTT initialized: {MQTT_BROKER}:{MQTT_PORT}")
                await asyncio.sleep(2)  # Allow time for connection
            else:
                logger.warning("Failed to connect to MQTT broker, falling back to simulator")
                mqtt_handler = None
        except Exception as e:
            logger.error(f"MQTT initialization failed: {e}, falling back to simulator")
            mqtt_handler = None
    
    asyncio.create_task(broadcaster())


@app.post("/signup", response_model=Token)
async def signup(user: UserCreate):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    try:
        create_user(user.username, user.password)
        access_token = create_access_token({"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except sqlite3.IntegrityError:
        # race: username inserted by another process between check and insert
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        logger.exception("Error creating user")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login", response_model=Token)
async def login(user: UserCreate):
    try:
        row = get_user(user.username)
        if not row:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        if not verify_password(user.password, row["password_hash"]):
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        access_token = create_access_token({"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during login")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            # keep connection alive; client may send pings or commands
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in clients:
            clients.remove(websocket)


@app.post("/start")
async def start(authorization: Optional[str] = Header(None)):
    user = None
    if authorization:
        try:
            token = authorization.split(" ", 1)[1] if " " in authorization else authorization
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user = payload.get("sub")
        except Exception:
            user = None
    logger.info("Start requested by %s", user or "anonymous")
    sim.start()
    return {"status": "started", "actor": user}


@app.post("/stop")
async def stop(authorization: Optional[str] = Header(None)):
    user = None
    if authorization:
        try:
            token = authorization.split(" ", 1)[1] if " " in authorization else authorization
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user = payload.get("sub")
        except Exception:
            user = None
    logger.info("Stop requested by %s", user or "anonymous")
    sim.stop()
    return {"status": "stopped", "actor": user}


@app.post("/set_speed/{rpm}")
async def set_speed(rpm: float, authorization: Optional[str] = Header(None)):
    user = None
    if authorization:
        try:
            token = authorization.split(" ", 1)[1] if " " in authorization else authorization
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user = payload.get("sub")
        except Exception:
            user = None
    logger.info("Set speed to %s requested by %s", rpm, user or "anonymous")
    sim.set_speed(rpm)
    return {"status": "ok", "rpm": sim.rpm, "actor": user}


@app.get("/")
async def root():
    return HTMLResponse("Simulator backend running. Connect via websocket at /ws")
