import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import logging

from backend.simulator import Simulator
from backend.mqtt_handler import MQTTHandler, mqtt_data_aggregator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            # If USE_MQTT is true, only MQTT data is sent.
            # If USE_MQTT is false, no data will be sent by the broadcaster.
            
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
                logger.warning("Failed to connect to MQTT broker. Dashboard will wait for ESP32 signal.")
                # mqtt_handler is kept, but its is_connected() will be false, so no data is sent.
        except Exception as e:
            logger.error(f"MQTT initialization failed: {e}. Dashboard will wait for ESP32 signal.")
            # mqtt_handler is kept, but its is_connected() will be false, so no data is sent.
    
    asyncio.create_task(broadcaster())


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
async def start():
    logger.info("Start requested")
    sim.start()
    return {"status": "started"}


@app.post("/stop")
async def stop():
    logger.info("Stop requested")
    sim.stop()
    return {"status": "stopped"}


@app.post("/set_speed/{rpm}")
async def set_speed(rpm: float):
    logger.info("Set speed to %s requested", rpm)
    sim.set_speed(rpm)
    return {"status": "ok", "rpm": sim.rpm}


@app.get("/")
async def root():
    return HTMLResponse("Simulator backend running. Connect via websocket at /ws")
