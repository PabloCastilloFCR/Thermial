#!/usr/bin/env python3
"""
Thermial simple controller (MQTT) — with valve sequencing

Controlador simple por MQTT que, cada INTERVAL (por defecto 60 s), lee el último
estado publicado por el lazo Thermial (STATUS_TOPIC) y decide encender/apagar
bomba1 y calentador para alcanzar una temperatura objetivo en el estanque.

NOVEDAD: antes de activar la bomba, el controlador asegura que la válvula 1 esté
abierta. Si no lo está, publica la orden de apertura y espera hasta VALVE_WAIT
segundos a que el estado reportado indique que la válvula quedó abierta. Si la
válvula no se abre en el tiempo máximo, el controlador NO arrancará la bomba ni
el calentador y registrará una advertencia.

Comportamiento resumido:
- Si temp < (target - hysteresis): asegurar valve1 abierta → encender pump1 y heater
- Si temp > (target + hysteresis): apagar heater y pump1, y cerrar valve1
- Dentro de la banda de histéresis: mantener estado actual (no cambiar)
- Publica resumen de control en CONTROLLER_TOPIC
- Evita publicar comandos redundantes comparando con desired_state

Uso:
  python3 controller_simple_with_valve.py --broker 192.168.2.73 --target 55 \
    --interval 60 --pump 60 --heater 80 --valve-topic thermial/valve1/cmd

Requisitos:
- Python 3.x
- paho-mqtt (`pip3 install paho-mqtt`)
"""

import argparse
import json
import logging
import time
from datetime import datetime

import paho.mqtt.client as mqtt

# ----------------------
# Argumentos / Defaults
# ----------------------
parser = argparse.ArgumentParser(description="Thermial simple MQTT controller with valve sequencing")
parser.add_argument("--broker", "-b", default="192.168.2.35", help="MQTT broker host (IP o hostname)")
parser.add_argument("--port", "-p", default=1883, type=int, help="MQTT broker port")
parser.add_argument("--status-topic", default="thermial/status", help="Topic donde se publica el estado JSON")
parser.add_argument("--pump-topic", default="thermial/pump1/cmd", help="Topic de comando para bomba1")
parser.add_argument("--heater-topic", default="thermial/calentador/cmd", help="Topic de comando para calentador")
parser.add_argument("--valve-topic", default="thermial/valve1/cmd", help="Topic de comando para válvula 1")
parser.add_argument("--controller-topic", default="thermial/controller/status", help="Topic para publicar estado del controlador")
parser.add_argument("--target", "-t", default=33.0, type=float, help="Temperatura objetivo en °C")
parser.add_argument("--interval", "-i", default=30, type=int, help="Intervalo de muestreo / control en segundos")
parser.add_argument("--pump", default=100, type=int, help="Porcentaje de bomba cuando se activa (0-100)")
parser.add_argument("--heater", default=100, type=int, help="Porcentaje de calentador cuando se activa (0-100)")
parser.add_argument("--hysteresis", default=0.5, type=float, help="Histéresis en °C (para evitar chatter)")
parser.add_argument("--timeout", default=180, type=int, help="Tiempo máximo (s) que se acepta como 'estado reciente'")
parser.add_argument("--valve-wait", default=20, type=int, help="Segundos a esperar a que la válvula reporte 'abierta' antes de abortar")
parser.add_argument("--username", default=None, help="Usuario MQTT (opcional)")
parser.add_argument("--password", default=None, help="Password MQTT (opcional)")
parser.add_argument("--client-id", default="thermial_simple_controller", help="Client ID MQTT")
args = parser.parse_args()

BROKER_HOST = args.broker
BROKER_PORT = args.port
STATUS_TOPIC = args.status_topic
PUMP_TOPIC = args.pump_topic
HEATER_TOPIC = args.heater_topic
VALVE_TOPIC = args.valve_topic
CONTROLLER_TOPIC = args.controller_topic

TARGET_TEMP = max(25, min(40, args.target))
INTERVAL = args.interval
PUMP_PERCENT = max(0, min(100, args.pump))
HEATER_PERCENT = max(0, min(100, args.heater))
HYST = args.hysteresis
TIMEOUT = args.timeout  # segundos para considerar last_status "fresh"
VALVE_WAIT = args.valve_wait  # segundos a esperar a que valve1 reporte abierta

# ----------------------
# Logging
# ----------------------
logger = logging.getLogger("thermial_controller")
handler = logging.StreamHandler()
fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
handler.setFormatter(logging.Formatter(fmt))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Archivo
file_handler = logging.FileHandler("thermial_controller.log", mode="a")  # "w" sobrescribe cada vez, usa "a" si quieres acumular
file_handler.setFormatter(logging.Formatter(fmt))
logger.addHandler(file_handler)

# ----------------------
# Estado global
# ----------------------
last_status = None        # último dict JSON recibido
last_status_ts = None     # datetime del último status recibido
desired_state = {         # estado deseado para evitar publicaciones repetidas
    "pump": 0,
    "heater": 0,
    # guardaremos la valve como por módulo: 'valve1': 0/1
}

# ----------------------
# MQTT callbacks
# ----------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Conectado al broker MQTT {BROKER_HOST}:{BROKER_PORT} (rc={rc})")
        client.subscribe(STATUS_TOPIC, qos=1)
        logger.info(f"Suscrito a {STATUS_TOPIC}")
    else:
        logger.error(f"Fallo conexion MQTT, rc={rc}")

def on_message(client, userdata, msg):
    global last_status, last_status_ts
    topic = msg.topic
    payload_bytes = msg.payload
    try:
        payload = payload_bytes.decode()
    except Exception:
        payload = None

    if topic == STATUS_TOPIC:
        try:
            data = json.loads(payload)
            last_status = data
            last_status_ts = datetime.now()
            logger.debug(f"Status recibido a las {last_status_ts.isoformat()}")
        except Exception as e:
            logger.warning(f"No se pudo parsear JSON del status: {e}. Payload raw: {payload_bytes!r}")
    else:
        logger.debug(f"Mensaje en topic no esperado: {topic}")

# ----------------------
# Helpers
# ----------------------
def read_estanque_temp(status_dict):
    """Extrae la temperatura representativa del estanque (promedio temp3/temp4 si existen)."""
    if not status_dict:
        return None
    est = status_dict.get("estanque") or {}
    t3 = est.get("temp3")
    t4 = est.get("temp4")
    def to_float(x):
        try:
            return float(x)
        except Exception:
            return None
    ft3 = to_float(t3)
    ft4 = to_float(t4)
    if ft3 is not None and ft4 is not None:
        return (ft3 + ft4) / 2.0
    if ft3 is not None:
        return ft3
    if ft4 is not None:
        return ft4
    return None

def read_valve_state_from_status(status_dict, valve_module_name="valve1"):
    """
    Dado el dict de status, intenta leer el campo que expresa el estado de la válvula 1.
    Se espera que en status exista status['valvulas']['valve1_state'] == 1 o 0.
    valve_module_name: 'valve1' o 'valvula1' dependiendo de tu convención.
    """
    if not status_dict:
        return None
    valv = status_dict.get("valvulas") or {}
    # intentamos claves comunes: f"{valve_module_name}_state" y con 'valvula' prefijo
    key1 = f"{valve_module_name}_state"          # e.g., 'valve1_state'
    if key1 in valv:
        try:
            return int(valv[key1])
        except Exception:
            return None
    # fallback: buscar cualquier clave que contenga 'valve1' o 'valvula1'
    for k, v in valv.items():
        if valve_module_name in k or valve_module_name.replace('valve','valvula') in k:
            try:
                return int(v)
            except Exception:
                return None
    return None

def publish_cmd(client, topic, value):
    """Publica un comando (solo si cambia respecto a desired_state para evitar spam)."""
    global desired_state
    # detectar key para desired_state
    key = None
    tparts = topic.split("/")
    if len(tparts) >= 2:
        module = tparts[1]  # ej 'pump1' o 'valve1' o 'calentador'
    else:
        module = topic
    if "pump" in module or "bomba" in module:
        key = "pump"
    elif "calentador" in module or "heater" in module:
        key = "heater"
    elif "valve" in module or "valvula" in module:
        key = module  # e.g., 'valve1' -> store per-module
    # comparar con estado deseado
    try:
        ival = int(value)
    except Exception:
        logger.warning(f"Intentando publicar valor no entero {value} en {topic}")
        return
    if key:
        if desired_state.get(key) == ival:
            logger.debug(f"No se publica en {topic}: valor {ival} igual al deseado")
            return
        desired_state[key] = ival
    client.publish(topic, payload=str(ival), qos=1, retain=False)
    logger.info(f"Publicado cmd {topic} = {ival}")

def wait_for_valve_open(timeout_sec=VALVE_WAIT, poll_interval=1):
    """
    Espera hasta que la última status reportada indique que valve1 está abierta.
    Retorna True si se abre dentro del timeout, False si no o si last_status es None.
    """
    now = datetime.now()
    end = now.timestamp() + timeout_sec
    valve_module_name = VALVE_TOPIC.split("/")[1] if "/" in VALVE_TOPIC else "valve1"
    while datetime.now().timestamp() < end:
        # si no hay status aún, esperamos poll_interval y continuamos
        if last_status is None:
            time.sleep(poll_interval)
            continue
        # comprobar frescura
        if last_status_ts is None:
            time.sleep(poll_interval)
            continue
        age = (datetime.now() - last_status_ts).total_seconds()
        if age > TIMEOUT:
            logger.warning("Status stale mientras se esperaba apertura de válvula (age %.0f s).", age)
            return False
        state = read_valve_state_from_status(last_status, valve_module_name)
        if state is None:
            # no hay info clara de la válvula en el status
            time.sleep(poll_interval)
            continue
        if int(state) == 1:
            logger.debug("Válvula reporta ABIERTA.")
            return True
        # todavía cerrada; esperar
        time.sleep(poll_interval)
    logger.warning("Timeout esperando que la válvula se abra.")
    return False

def publish_controller_status(client, temp, action, reason):
    """Publica un resumen del estado del controlador para monitorización"""
    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": TARGET_TEMP,
        "temp": temp,
        "pump_cmd": desired_state.get("pump"),
        "heater_cmd": desired_state.get("heater"),
        "valve_cmd": desired_state.get(VALVE_TOPIC.split("/")[1]),
        "action": action,
        "reason": reason
    }
    client.publish(CONTROLLER_TOPIC, payload=json.dumps(payload), qos=1, retain=True)
    logger.debug(f"Published controller status: {payload}")

# ----------------------
# Setup MQTT client
# ----------------------
client = mqtt.Client(client_id=args.client_id, protocol=mqtt.MQTTv311)
if args.username:
    client.username_pw_set(args.username, args.password)

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
client.loop_start()

# ----------------------
# Main control loop
# ----------------------
try:
    logger.info("Controlador Thermial iniciado. Intervalo=%ds target=%.2f°C hyst=%.2f°C.",
                INTERVAL, TARGET_TEMP, HYST)

    # Estado inicial (asumir todo apagado)
    desired_state["pump"] = 0
    desired_state["heater"] = 0
    # inicial valve key
    valve_module_key = VALVE_TOPIC.split("/")[1] if "/" in VALVE_TOPIC else "valve1"
    desired_state[valve_module_key] = 0

    while True:
        # esperar INTERVAL segundos por pasos para responder a SIGINT
        slept = 0
        while slept < INTERVAL:
            time.sleep(1)
            slept += 1

        # verificamos frescura del último status
        now = datetime.now()
        if last_status_ts is None:
            logger.warning("No se ha recibido status aún. No se actúa.")
            publish_controller_status(client, None, "idle", "no_status")
            continue
        age = (now - last_status_ts).total_seconds()
        if age > TIMEOUT:
            logger.warning("Último status demasiado antiguo (%.0f s). No se actúa.", age)
            publish_controller_status(client, None, "idle", "stale_status")
            continue

        # extrae temperatura representativa del estanque
        temp = read_estanque_temp(last_status)
        if temp is None:
            logger.warning("No se encontró temperatura del estanque en el status. No se actúa.")
            publish_controller_status(client, None, "idle", "no_temp")
            continue

        # control con histéresis
        lower = TARGET_TEMP - HYST
        upper = TARGET_TEMP + HYST

        action = "none"
        reason = ""

        if temp < lower:
            # necesitamos calentar: PRIMERO asegurar valve1 abierta
            logger.info("Temp %.2f < lower %.2f -> intentar calentar. Asegurando válvula abierta...", temp, lower)
            # publicar orden de abrir válvula (1)
            publish_cmd(client, VALVE_TOPIC, 1)
            # esperar confirmación de apertura
            ok = wait_for_valve_open(timeout_sec=VALVE_WAIT, poll_interval=1)
            if not ok:
                action = "abort_heating"
                reason = "valve_not_open"
                logger.warning("No se abrió la válvula en el tiempo esperado. Abortando arranque de bomba y calentador.")
                publish_controller_status(client, temp, action, reason)
                continue  # pasar a siguiente ciclo sin encender pump/heater

            # válvula abierta -> ahora activar bomba y calentador
            publish_cmd(client, PUMP_TOPIC, PUMP_PERCENT)
            publish_cmd(client, HEATER_TOPIC, HEATER_PERCENT)
            action = "heating_on"
            reason = f"temp {temp:.2f} < lower {lower:.2f}"
            logger.info("Activando bomba y calentador: pump=%d %% heater=%d %%", PUMP_PERCENT, HEATER_PERCENT)

        elif temp > upper:
            # temperatura superó el target: apagar heater y pump, y cerrar válvula
            logger.info("Temp %.2f > upper %.2f -> apagar calefacción y bomba.", temp, upper)
            publish_cmd(client, HEATER_TOPIC, 0)
            publish_cmd(client, PUMP_TOPIC, 0)
            # cerrar válvula
            publish_cmd(client, VALVE_TOPIC, 0)
            action = "heating_off"
            reason = f"temp {temp:.2f} > upper {upper:.2f}"
            logger.info("Bomba y calentador apagados; solicitada cierre de válvula.")

        else:
            # dentro de la banda de histéresis: mantener estado actual
            action = "holding"
            reason = f"temp {temp:.2f} dentro de [{lower:.2f}, {upper:.2f}]"
            logger.info("Temperatura dentro de la banda de histéresis: %.2f (manteniendo estado)", temp)

        # publicar estado del controlador
        publish_controller_status(client, temp, action, reason)

except KeyboardInterrupt:
    logger.info("Interrupción por usuario. Desconectando y dejando actuadores en estado seguro.")
    try:
        publish_cmd(client, HEATER_TOPIC, 0)
        publish_cmd(client, PUMP_TOPIC, 0)
        publish_cmd(client, VALVE_TOPIC, 0)
    except Exception:
        pass

finally:
    client.loop_stop()
    client.disconnect()
    logger.info("Controlador detenido.")
