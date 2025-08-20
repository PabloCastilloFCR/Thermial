"""
Thermial MQTT status publisher (docstring)

Este script publica periódicamente el estado del lazo "Thermial" al broker MQTT.
Lee el estado desde una única instancia de la clase Loop (módulo thermial)
y publica un JSON en el topic STATUS_TOPIC (por defecto: "thermial/status").

Resumen de funcionamiento

Ajusta el sys.path para permitir importar thermial desde la carpeta custom_code
situada un nivel por encima del script.

Crea una instancia de Loop (controlador del lazo: bombas, válvulas, calentador, etc.).

En un bucle infinito:

Llama a loop.update_status_dict_mqtt() para obtener un diccionario anidado con
todas las variables de estado.

Serializa ese diccionario a JSON.

Publica el JSON en el topic thermial/status con qos=1 y retain=True.

Manejo de parada con KeyboardInterrupt: detiene el loop MQTT y cierra la conexión.

Configuración importante

BROKER_HOST : IP/hostname del broker MQTT (ej. la Raspberry Pi).

BROKER_PORT : puerto del broker (por defecto 1883).

STATUS_TOPIC : topic donde se publica el estado (por defecto "thermial/status").

Requisitos

Python 3.x

paho-mqtt (pip3 install paho-mqtt)

El paquete thermial accesible en ../custom_code/thermial relativo a este script.

Buenas prácticas y notas

Ejecuta este script en la Raspberry Pi para minimizar latencia con el hardware I2C,
o en la misma máquina donde exista acceso seguro al bus.

retain=True asegura que nuevos suscriptores reciben el último estado inmediatamente.

Para producción, considera:

Ejecutar como servicio systemd.

Usar autenticación en el broker (client.username_pw_set(...)) si Mosquitto requiere credenciales.

Usar logging en vez de print() para control de niveles (DEBUG/INFO/WARNING).

Manejar excepciones de lectura I2C en Loop para evitar publicar datos corruptos.
"""


import paho.mqtt.client as mqtt
import sys
import os
import time
import json

# Agrega la ruta de la carpeta custom_code al sys.path
# La línea siguiente navega un nivel hacia arriba (..),
# luego busca la carpeta 'custom_code'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'custom_code'))

# Ahora puedes importar el módulo thermial
from thermial import Loop

# 1. Parámetros de conexión
BROKER_HOST = "192.168.2.73"   # IP de tu RPi/Mosquitto
BROKER_PORT = 1883
STATUS_TOPIC = "thermial/status"

# 2. Crear y configurar cliente MQTT
client = mqtt.Client(client_id="thermial_publisher")
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
client.loop_start()

# 3. Instanciar tu controlador
loop = Loop(verbose=False)

try:
    while True:
        # 4. Genera el dict de estado
        status = loop.update_status_dict_mqtt()
        
        # 5. Serializa a JSON
        payload = json.dumps(status)
        
        # 6. Publica al topic
        client.publish(
            STATUS_TOPIC,
            payload=payload,
            qos=1,
            retain=True   # mantiene siempre el último estado
        )
        print(f"Publicado en {STATUS_TOPIC}: {payload}")
        
        # 7. Espera antes de la siguiente publicación
        time.sleep(2)   # cada 2 s, por ejemplo

except KeyboardInterrupt:
    print("Detenido por el usuario")

finally:
    client.loop_stop()
    client.disconnect()