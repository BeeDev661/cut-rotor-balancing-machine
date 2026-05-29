"""
MQTT Handler for ESP32 sensor data integration.
Subscribes to MQTT topics and makes data available to FastAPI via async queue.
"""

import asyncio
import json
import logging
import os
from typing import Callable, Optional
from datetime import datetime

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTHandler:
    def __init__(
        self,
        broker_address: str,
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False,
        client_id: str = "dashboard_backend",
    ):
        """
        Initialize MQTT handler.
        
        Args:
            broker_address: MQTT broker hostname/IP
            broker_port: MQTT broker port (default 1883)
            username: MQTT username (optional)
            password: MQTT password (optional)
            use_tls: Enable TLS encryption
            client_id: MQTT client ID
        """
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.client_id = client_id
        self.client = None
        self.connected = False
        self.data_callback: Optional[Callable] = None
        
    def set_data_callback(self, callback: Callable):
        """Set callback function for received data."""
        self.data_callback = callback
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            logger.info("MQTT connected successfully")
            self.connected = True
            # Subscribe to sensor topics
            client.subscribe("esp32/accelerometer")
            client.subscribe("esp32/rpm")
            client.subscribe("esp32/status")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False
            
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        self.connected = False
        logger.warning(f"MQTT disconnected with code {rc}")
        
    def _on_message(self, client, userdata, msg):
        """Callback for MQTT message received."""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.debug(f"MQTT message from {topic}: {payload}")
            
            # Call data callback if registered
            if self.data_callback:
                asyncio.create_task(
                    self.data_callback(topic=topic, data=payload)
                )
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode JSON from topic {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
            
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client = mqtt.Client(client_id=self.client_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
                
            if self.use_tls:
                self.client.tls_set()
                
            logger.info(f"Connecting to MQTT broker at {self.broker_address}:{self.broker_port}")
            self.client.connect(self.broker_address, self.broker_port, keepalive=60)
            self.client.loop_start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker."""
        return self.connected


async def mqtt_data_aggregator(mqtt_handler: MQTTHandler):
    """
    Aggregates MQTT data into a single message format compatible with WebSocket clients.
    Returns the aggregated data that should be sent to connected WebSocket clients.
    """
    latest_data = {
        "timestamp": None,
        "rpm": 0.0,
        "sample_rate": 2048,
        "acc": [],
    }
    
    async def on_mqtt_data(topic: str, data: dict):
        """Handle incoming MQTT data."""
        try:
            if topic == "esp32/accelerometer":
                # Expect: {"acc": [a1, a2, ...], "sample_rate": 2048, "timestamp": <unix>}
                latest_data["acc"] = data.get("acc", [])
                latest_data["sample_rate"] = data.get("sample_rate", 2048)
                latest_data["timestamp"] = data.get("timestamp", datetime.now().timestamp())
                
            elif topic == "esp32/rpm":
                # Expect: {"rpm": 1500.0}
                latest_data["rpm"] = float(data.get("rpm", 0.0))
                
        except Exception as e:
            logger.error(f"Error processing MQTT data: {e}")
    
    mqtt_handler.set_data_callback(on_mqtt_data)
    return latest_data
