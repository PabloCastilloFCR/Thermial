#!/usr/bin/env python3

"""
Thermial MQTT controller — publisher & command listener (docstring)

Este script centraliza la lógica de control y telemetría para el lazo "Thermial".
Se ejecuta en la Raspberry Pi (o en una máquina con acceso al bus I2C) y realiza
las siguientes funciones principales:

Crea UNA SOLA instancia de la clase Loop (módulo thermial) que encapsula
el control de bombas, válvulas, calentador, estanque y disipador. Esto evita
conflictos entre múltiples instancias que intenten escribir sobre el hardware.

Conexión MQTT:

Se conecta a un broker MQTT (BROKER_HOST / BROKER_PORT).

Se suscribe al topic wildcard thermial/+/cmd para recibir comandos dirigidos
a cualquier módulo (p. ej. thermial/pump1/cmd).

Publica periódicamente el estado completo del lazo en thermial/status como
JSON (retain=True, qos=1) para que nuevos suscriptores obtengan el último valor.

Despacho de comandos:

Cuando llega un mensaje en thermial/<module>/cmd, se extrae <module> y
el payload y se llama a handle_command(module, payload).

handle_command mapea módulos a métodos de la instancia Loop, validando
el payload (se espera entero) y ejecutando la acción correspondiente
(p. ej. set_potencia_bomba, set_potencia_calentador, abrir/cerrar válvula, etc.).

Logging:

Se configura un logger ("mqtt") con handler de consola.

Ajusta la verbosidad cambiando logger.setLevel(...) (DEBUG, INFO, WARNING).

Robustez y cierre:

client.loop_start() corre el cliente MQTT en background.

Al recibir KeyboardInterrupt se detiene el loop MQTT y se llama a loop.stop()
para dejar el sistema en un estado seguro (actuadores en 0 / válvulas cerradas).

Parámetros y configuración

BROKER_HOST : dirección IP o hostname del broker MQTT (por defecto: "192.168.2.73").

BROKER_PORT : puerto del broker (por defecto: 1883).

STATUS_TOPIC : topic donde se publica el JSON de estado (por defecto: "thermial/status").

CMD_TOPIC_WC : wildcard para comandos (por defecto: "thermial/+/cmd").

Requisitos

Python 3.x

paho-mqtt (pip3 install paho-mqtt)

El paquete thermial localizado en ../custom_code/thermial respecto a este script.

Notas de seguridad y operación

Si tu broker requiere autenticación, llama a client.username_pw_set(user, pass)
antes de connect(...).

retain=True en el topic de status hace que nuevos clientes reciban inmediatamente
el último estado publicado.

Ejecuta este script como servicio (systemd) para producción y considera usar
monitoreo y restart automático.

Maneja excepciones dentro de la clase Loop para evitar publicar datos inválidos.

Ejemplo de ejecución

$ python3 this_script.py
"""

import os
import sys
import time
import json
import logging
import paho.mqtt.client as mqtt
from datetime import datetime

# ——————————————————————————————————————————
# Ajuste de ruta para tu módulo Thermial
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'custom_code'))
from thermial import Loop
# ——————————————————————————————————————————

BROKER_HOST  = "192.168.2.35"   # IP de tu Pi
BROKER_PORT  = 1883
STATUS_TOPIC = "thermial/status"
CMD_TOPIC_WC = "thermial/+/cmd"  # wildcard para comandos

logger = logging.getLogger("mqtt")          # choose a namespace for your module
handler = logging.StreamHandler()           # print to stdout
fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
handler.setFormatter(logging.Formatter(fmt))
logger.addHandler(handler)

# Toggle verbosity here:
logger.setLevel(logging.WARNING)    # verbose: INFO, DEBUG

# 1) Crea UNA SOLA instancia de Loop
loop = Loop(verbose=False)

# 2) Callbacks MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Conectado a MQTT, suscribiendo comandos…")
        client.subscribe(CMD_TOPIC_WC, qos=1)
    else:
        logger.error(f"Falló conexión MQTT, rc={rc}")

def on_message(client, userdata, msg):
    # topic = "thermial/<module>/cmd"
    _, module, _ = msg.topic.split("/")
    payload = msg.payload.decode()
    handle_command(module, payload)

# 3) Mapea y despacha comandos a métodos de tu Loop
def handle_command(module, payload):
    try:
        val = int(payload)
    except ValueError:
        logger.debug("ValueError")
        logger.warning(f"Payload inválido para {module}: {payload}")
        return

    if module.startswith("pump"):
        logger.debug("Bomba")
        num = int(module[-1])
        loop.set_potencia_bomba(number=num, potencia=val)

    elif module == "heater":
        logger.debug("Calentador")
        loop.set_potencia_calentador(val)

    elif module.startswith("valve"):
        logger.debug("Valvulas")
        num = int(module[-1])
        if val:
            loop.set_abrir_valvula(num)
        else:
            loop.set_cerrar_valvula(num)

    elif module == "radiator":
        logger.debug("Disipador")
        loop.set_potencia_disipador(val)

    else:
        logger.debug("Ninguno")
        logger.warning(f"Módulo desconocido en cmd: {module}")

# 4) Configura cliente MQTT y lo arranca
client = mqtt.Client(client_id="thermial_node", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
client.loop_start()

# 5) Bucle principal: publicar status cada X segundos
try:
    print("Ejecutando Loop. Publicando Status.")
    while True:
        status = loop.update_status_dict_mqtt()
        payload = json.dumps(status)
        client.publish(STATUS_TOPIC, payload=payload, qos=1, retain=True)
        logger.debug("Publicando Status")
        time.sleep(5)   # intervalo de publicación

except KeyboardInterrupt:
    pass

finally:
    client.loop_stop()
    client.disconnect()
    loop.stop()  # apaga todos los actuadores de forma segura
