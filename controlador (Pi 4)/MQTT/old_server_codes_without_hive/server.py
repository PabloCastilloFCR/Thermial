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

from thermial_error_handling import Loop as BaseLoop

class ServerLoop(BaseLoop):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "IDLE"
        print("[ServerLoop] Error handling active")


    def on_message(self, client, userdata, msg):
        if self.errors:
            logger.warning(f"Loop error active, ignoring comand {msg.payload.decode()}")
            return
        # topic = "thermial/<module>/cmd"
        _, module, _ = msg.topic.split("/")
        payload = msg.payload.decode()
        self.handle_command(module, payload)

    # 3) Mapea y despacha comandos a métodos de tu Loop
    def handle_command(self, module, payload):
        logger.debug(f"Received command for module='{module}', payload='{payload}'")
        try:
            val = int(payload)
        except ValueError:
            logger.debug("ValueError")
            logger.warning(f"Invalid payload for module '{module}': '{payload}' (expected integer)")
            return
        
        if self.errors:
            logger.error(f"System stopped due to errors: {self.errors}")
            self.stop()
            return
        

        if module.startswith("pump"):
            num = int(module[-1])
            logger.debug(f"Pump command received for pump{num} with value {val}")
            logger.info(f"Set pump {num} to {val}% via MQTT")
            self.set_power_pump(num, val) 

        elif module == "heater1":
            logger.debug(f"Heater1 command: set power to {val}")
            self.set_power_heater1(val)

        elif module == "heater2":
            logger.debug(f"Heater2 command: set power to {val}")
            self.set_power_heater2(val)

        elif module.startswith("valve"):
            num = int(module[-1])
            logger.debug(f"Valve command received for valve{num}, payload={val}")
            if val:
                logger.info(f"Open valve{num} via MQTT")
                self.set_open_valve(num)
            else:
                logger.info(f"Close valve{num} via MQTT")
                self.set_close_valve(num)

        elif module == "radiator":
            logger.debug(f"Radiator command: set power to {val}")
            self.set_power_radiator1(val) 

        elif module == "stop":
            logger.debug("Stop command received, shutting down the loop")
            self.stop()

        else:
            logger.debug(f"No command found for module '{module}'")
            logger.warning(f"Unknown module in cmd: '{module}'")

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
logger.setLevel(logging.DEBUG)    # verbose: WARNING, INFO, DEBUG

#crear un objeto server loop, que contiene el loop normal, que tenga el manejo de errores con metodos on_message y handle_command
# 1) Crea UNA SOLA instancia de Loop
loop = ServerLoop(verbose=False)

# 2) Callbacks MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Conectado a MQTT, suscribiendo comandos…")
        client.subscribe(CMD_TOPIC_WC, qos=1)
    else:
        logger.error(f"Falló conexión MQTT, rc={rc}")


# 4) Configura cliente MQTT y lo arranca
client = mqtt.Client(client_id="thermial_node", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = loop.on_message
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
client.loop_start()

# 5) Bucle principal: publicar status cada X segundos
try:
    print("Running Loop. Publishing Status.")
    loop.status = "ACTIVE"
    error_reported = False

    while True:
        if loop.status == "ACTIVE":
            status_ok, data = loop.update_status_dict_mqtt()
            data["status"] = "ACTIVE"

        if status_ok == False:
            loop.status = "ERROR"
            if not error_reported:
                logger.error(f"Error detected, {loop.errors['error_type']}, stopping actuators")
                loop.stop()
            #MQTT continues, but without active actuators
                payload = json.dumps({"status": "ERROR", "errors": loop.errors})
                client.publish(STATUS_TOPIC, payload=payload, qos=1, retain=True)
                error_reported = True
            continue

        else:
            payload = json.dumps(data)
            logger.debug(f"Publishing status: {payload}")
            client.publish(STATUS_TOPIC, payload=payload, qos=1, retain=True)

        time.sleep(5)  # publish interval
        
except KeyboardInterrupt:
    print("Server detenido")
    pass

finally:
    client.loop_stop()
    client.disconnect()
    loop.stop()  # apaga todos los actuadores de forma segura