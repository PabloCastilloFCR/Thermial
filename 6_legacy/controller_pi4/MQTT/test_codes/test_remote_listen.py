#!/usr/bin/env python3

"""
Thermial MQTT status listener (docstring)

Este script es un cliente MQTT simple (Python + paho-mqtt) diseñado para suscribirse
al topic que publica el estado del lazo "Thermial" en la Raspberry Pi y mostrar
por consola el JSON recibido en forma legible.

Funcionamiento

Conexión: se conecta a un broker MQTT (definido en BROKER_HOST/BROKER_PORT).

Suscripción: al conectarse, se suscribe al topic definido en STATUS_TOPIC.

Recepción: cuando llega un mensaje en ese topic, intenta decodificar el payload
como JSON y lo imprime formateado (indentado). Si el payload no es JSON,
imprime el payload crudo y un aviso.

Ejecución continua: usa client.loop_forever() para mantener la conexión y
reintentar la reconexión ante cortes.

Uso / configuración

Ajusta BROKER_HOST a la IP o hostname del broker (p. ej. la Raspberry Pi).

Ajusta BROKER_PORT si tu broker no usa el puerto 1883 por defecto.

Ajusta STATUS_TOPIC si tu publicador usa otro topic (por defecto: "thermial/status").

Requisitos

Python 3.x

paho-mqtt (instalar con pip3 install paho-mqtt)

Ejemplo de ejecución

$ python3 remote_listen.py

Notas adicionales

client.loop_forever() intenta reconectar automáticamente en la mayoría de
las condiciones; si necesitas un control más fino sobre reconexiones, usar
loop_start() + lógica de reconexión explícita puede ser más apropiado.

Si tu broker requiere autenticación, usa client.username_pw_set(user, pass)
antes de connect(...).

Este script imprime con print(); para producción considera usar logging.
"""

import json
import paho.mqtt.client as mqtt

# 1. Configura aquí la IP de tu Raspberry Pi
BROKER_HOST = "192.168.2.35"   # Reemplaza con la IP real de tu Pi
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