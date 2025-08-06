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