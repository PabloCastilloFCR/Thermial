#!/usr/bin/env python3
import json
import paho.mqtt.client as mqtt

# 1. Configura aquí la IP de tu Raspberry Pi
BROKER_HOST = "192.168.2.73"   # Reemplaza con la IP real de tu Pi
BROKER_PORT = 1883
STATUS_TOPIC = "thermial/status"

# 2. Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado al broker MQTT")
        client.subscribe(STATUS_TOPIC, qos=1)
        print(f"Suscrito a: {STATUS_TOPIC}")
    else:
        print(f"Error de conexión, código RC={rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print("Estado recibido:")
        # formatea bonito el JSON
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(f"Mensaje no JSON en {msg.topic}: {msg.payload!r}")

# 3. Inicializa el cliente MQTT
client = mqtt.Client(client_id="laptop-suscriptor")
client.on_connect = on_connect
client.on_message = on_message

# 4. Conecta y arranca el loop
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
client.loop_forever()