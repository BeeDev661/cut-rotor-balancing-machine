import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional

import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from passlib.context import CryptContext
import logging

# IMPORT SUPABASE CLIENT
from supabase import create_client, Client

from backend.simulator import Simulator
from backend.mqtt_handler import MQTTHandler, mqtt_data_aggregator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()
sim = Simulator()

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "*").split(",") # Allow specific origins or all
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ============ Authentication & Cloud DB ============
# Replace SQLite with Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().strip("'").strip('"')
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip().strip("'").strip('"')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")

try:
    # Connect to cloud database
    supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info(f"Supabase client initialized with URL: {SUPABASE_URL[:20]}...")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

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


# ============ Cloud Database Actions ============
def get_user(username: str) -> Optional[dict]:
    """Fetches a user profile from the cloud Supabase database."""
    try:
        response = supabase_client.table("users").select("*").eq("username", username).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Database read error: {e}")
        return None


def create_user(username: str, password: str):
    """Inserts a new user record into the cloud database."""
    now = time.time()
    hashed_password = pwd_context.hash(password)
    
    # Check if user already exists to prevent duplicate rows
    if get_user(username):
        raise HTTPException(status_code=400, detail="Username already exists")
        
    try:
        supabase_client.table("users").insert({
            "username": username,
            "password_hash": hashed_password,
            "created_at": now
        }).execute()
    except Exception as e:
        logger.error(f"Database insert error: {e}")
        raise HTTPException(status_code=500, detail="Could not register account.")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
            
            if USE_MQTT and mqtt_handler and mqtt_handler.is_connected() and mqtt_latest_data:
                if mqtt_latest_data.get("acc"):
                    data_to_send = json.dumps(mqtt_latest_data)
                    
            if not data_to_send and sim.running and clients:
                msg = await sim.stream_chunk(duration=0.1)
                data_to_send = msg
            
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
            
        await asyncio.sleep(0.05)  # Slightly reduced frequency to ease channel load


@app.on_event("startup")
async def startup_event():
    global mqtt_handler, mqtt_latest_data
    
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
                await asyncio.sleep(2)
            else:
                logger.warning("Failed to connect to MQTT broker, falling back to simulator")
                mqtt_handler = None
        except Exception as e:
            logger.error(f"MQTT initialization failed: {e}, falling back to simulator")
            mqtt_handler = None
    
    asyncio.create_task(broadcaster())


@app.post("/signup", response_model=Token)
async def signup(user: UserCreate):
    create_user(user.username, user.password)
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/login", response_model=Token)
async def login(user: UserCreate):
    try:
        user_record = get_user(user.username)
        if not user_record:
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        if not verify_password(user.password, user_record["password_hash"]):
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
            # Listening block + custom ping interval to prevent Heroku from dropping the line
            data = await asyncio.wait_for(websocket.receive_text(), timeout=20.0)
    except (WebSocketDisconnect, asyncio.TimeoutError):
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
