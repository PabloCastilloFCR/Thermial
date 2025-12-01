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
#import paho.mqtt.client as mqtt
import paho.mqtt.client as paho
from paho import mqtt
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
        
        #variables for user-management
        self.active_user = None # current registered user
        self.last_activity = None # timestamp of the last activity
        self.timeout_seconds = 21600 # 6 hours timeout

        print("[ServerLoop] Error handling active")
        print("[ServerLoop] User registration system active")

    def register_user(self, user_id, client):
        #registers a new client or denies access, when someone else is already registered
        if self.active_user is not None and self.active_user != user_id:
            logger.warning(f"Registration denied for '{user_id}': User'{self.active_user}' already registered.")
            response = {
                "status": "DENIED",
                "user_id": user_id,
                "reason": f"User '{self.active_user}' has active control",
                "timestamp": datetime.now().isoformat()
            }
            client.publish("thermial/register/response", json.dumps(response), qos=2)
            return False
        
        # register the new user
        self.active_user = user_id
        self.last_activity = time.time()
        logger.info(f"User '{user_id}' successfully registered and given control")

        response= {
            "status": "ACCEPTED",
            "user_id": user_id,
            "message": "Control granted",
            "timestamp": datetime.now().isoformat()
        }
        client.publish("thermial/register/response", json.dumps(response), qos=1, retain = True)
        return True
    
    def unregister_user(self, user_id, client):
        # logout of the current user, only if current user is the active user
        if self.active_user == user_id:
            logger.info(f"User '{user_id}' inactive, control released")
            #stops all actuators when user logs out
            logger.info("Stopping all actuators for safety.")
            self.set_power_pump(1, 0)
            self.set_power_pump(2, 0)
            self.set_power_heater1(0)
            self.set_power_heater2(0)
            self.set_power_radiator1(0)
            self.set_close_valve(1)
            self.set_close_valve(2)
            logger.info("All actuators stopped.")

            # <<< confirm Shutdown
            client.publish("thermial/shutdown/confirm", json.dumps({"status": "confirmed", "user_id": user_id}), qos=1)
            logger.info("✓ Shutdown confirmation sent to client")
            
            self.active_user = None
            self.last_activity = None

            response = {
                "status": "UNREGISTERED",
                "user_id": user_id,
                "message": "Control released",
                "timestamp": datetime.now().isoformat()
            }
            client.publish("thermial/register/response", json.dumps(response), qos=1)
            return True
        else:
            logger.warning(f"Unregister denied for '{user_id}': Not the active user.")
            return False

    def check_user_timeout(self):
        #checks if current user is inactive for a long time and logs out -> timeout
        if self.active_user and self.last_activity:
            elapsed = time.time() -self.last_activity
            if elapsed > self.timeout_seconds: #timeout check
                logger.warning(f"User '{self.active_user}' timed out after {elapsed:.0f}s inactivity")
                self.active_user = None
                self.last_activity = None
                return True # timeout happens
        return False # no timeout, or no user

    def on_message(self, client, userdata, msg):
        """
        Erweiterte Message-Handler für Registrierung und Befehle
        """
        topic = msg.topic
        payload = msg.payload.decode()
        
        # 1) Registrierungs-Topic
        if topic == "thermial/register":
            try:
                data = json.loads(payload)
                action = data.get("action")
                user_id = data.get("user_id")
                
                if not user_id:
                    logger.warning("Registration request without user_id")
                    return
                
                if action == "register":
                    self.register_user(user_id, client)
                elif action == "unregister":
                    ok = self.unregister_user(user_id, client)
                    if ok:
                        logger.info("User unregistered, actuators stopped safely.")
                    else: 
                        logger.warning("Unregister ignored: wrong user.")
                else:
                    logger.warning(f"Unknown registration action: {action}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in registration: {payload}")
            return
        
        # 2) Befehls-Topics (thermial/+/cmd)
        if "/cmd" in topic:
            # Prüfe ob Loop Fehler hat
            if self.errors:
                logger.warning(f"Loop error active, ignoring command {payload}")
                return
            
            # Timeout-Check
            self.check_user_timeout()
            
            # Prüfe ob ein User registriert ist
            if self.active_user is None:
                logger.warning(f"Command rejected: No user registered (topic: {topic})")
                return
            
            # Extrahiere User-ID aus dem Payload (erwarte Format: {"user_id": "...", "value": ...})
            try:
                data = json.loads(payload)
                sender_id = data.get("user_id")
                value = data.get("value")
                
                if not sender_id:
                    logger.warning(f"Command without user_id in payload: {payload}")
                    return
                
                # Prüfe ob Sender der registrierte User ist
                if sender_id != self.active_user:
                    logger.warning(f"Command rejected: User '{sender_id}' is not the active user (active: '{self.active_user}')")
                    return
                
                # Update last activity
                self.last_activity = time.time()
                
                # Extrahiere Modul aus Topic
                _, module, _ = topic.split("/")
                self.handle_command(module, str(value))
                
            except json.JSONDecodeError:
                # Fallback: Altes Format ohne JSON (nur für Kompatibilität)
                if self.active_user:
                    logger.warning("Command received in old format (no user_id), processing anyway")
                    _, module, _ = topic.split("/")
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
            logger.info(f"Set pump {num} to {val}% via MQTT (User: {self.active_user})")
            self.set_power_pump(num, val) 

        elif module == "heater1":
            logger.debug(f"Heater1 command: set power to {val} (User: {self.active_user})")
            self.set_power_heater1(val)

        elif module == "heater2":
            logger.debug(f"Heater2 command: set power to {val} (User: {self.active_user})")
            self.set_power_heater2(val)

        elif module.startswith("valve"):
            num = int(module[-1])
            logger.debug(f"Valve command received for valve{num}, payload={val} (User: {self.active_user})")
            if val:
                logger.info(f"Open valve{num} via MQTT (User: {self.active_user})")
                self.set_open_valve(num)
            else:
                logger.info(f"Close valve{num} via MQTT (User:{self.active_user})")
                self.set_close_valve(num)

        elif module == "radiator":
            logger.debug(f"Radiator command: set power to {val} (User: {self.active_user})")
            self.set_power_radiator1(val) 

        elif module == "stop":
            logger.debug("Stop command received, shutting down the loop")
            self.stop()

        else:
            logger.debug(f"No command found for module '{module}'")
            logger.warning(f"Unknown module in cmd: '{module}'")

# ——————————————————————————————————————————

#BROKER_HOST  = "192.168.2.35"   # IP de tu Pi
BROKER_HOST_HIVEMQ = "96916c26427f41a395170e4ee96828c6.s1.eu.hivemq.cloud"
#BROKER_PORT  = 1883
BROKER_PORT_HIVEMQ = 8883
STATUS_TOPIC = "thermial/status"
CMD_TOPIC_WC = "thermial/+/cmd"  # wildcard para comandos
REGISTER_TOPIC = "thermial/register" # topic for user ID request
HIVEMQ_USER = "thermialServer"
HIVEMQ_PASS = "Fcr.2025"

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
def on_connect(client, userdata, flags, rc, properties = None):
    if rc == 0:
        logger.info("Conectado a MQTT, suscribiendo comandos…")
        client.subscribe(CMD_TOPIC_WC, qos=1)
        client.subscribe(REGISTER_TOPIC, qos=1) 
    else:
        logger.error(f"Falló conexión MQTT, rc={rc}")


# 4) Configura cliente MQTT y lo arranca
#client = mqtt.Client(client_id="thermial_node", protocol=mqtt.MQTTv311)
client = paho.Client(client_id="thermial_node", protocol=paho.MQTTv5)
client.on_connect = on_connect
# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set(HIVEMQ_USER, HIVEMQ_PASS)
# connect to HiveMQ Cloud on port 8883
client.connect(BROKER_HOST_HIVEMQ, 8883)

client.on_message = loop.on_message
#client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

client.loop_start()

# 5) Bucle principal: publicar status cada X segundos
try:
    print("Running Loop. Publishing Status.")
    loop.status = "ACTIVE"
    error_reported = False

    while True:
        # Time Out check in the main loop
        loop.check_user_timeout()


        if loop.status == "ACTIVE":
            status_ok, data = loop.update_status_dict_mqtt()
            data["status"] = "ACTIVE"
            data["active_user"] = loop.active_user # user info in status

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
            logger.debug(f"Publishing status: {payload}\n")
            client.publish(STATUS_TOPIC, payload=payload, qos=1, retain=True)

        time.sleep(60)  # publish interval
        
except KeyboardInterrupt:
    print("Server detenido")
    pass

finally:
    client.loop_stop()
    client.disconnect()
    loop.stop()  # apaga todos los actuadores de forma segura