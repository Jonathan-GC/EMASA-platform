import paho.mqtt.client as mqtt
import json
from app.mqtt.handlers import handle_message
from app.persistence.mongo import get_db
import loguru
from app.settings import settings

BROKER_HOST = settings.BROKER_URL
BROKER_PORT = settings.BROKER_PORT
TOPIC = "applications/+/devices/+/event/up"

client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        loguru.logger.info("Connected to MQTT Broker!")
        client.subscribe(TOPIC)
        loguru.logger.info(f"Subscribed to topic: {TOPIC}")
    else:
        loguru.logger.error(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        db = userdata.get("db")
        loop = userdata.get("loop")
        handle_message(payload, db, loop)
    except Exception as e:
        loguru.logger.error(f"Error processing message: {e}")


def start_mqtt(db, loop):
    client.user_data_set({"db": db, "loop": loop})
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    loguru.logger.info("MQTT client started and running in background")
