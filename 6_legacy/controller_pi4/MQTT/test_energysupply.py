import paho.mqtt.client as paho 
from paho import mqtt 
import time 
import sys 
# --- HiveMQ configuration ---
BROKER_HOST_HIVEMQ = "96916c26427f41a395170e4ee96828c6.s1.eu.hivemq.cloud"
HIVEMQ_USER = "thermialServer"
HIVEMQ_PASS = "Fcr.2025"
BROKER_PORT_HIVEMQ = 8883
TOPIC_ENERGY_SUPPLY = "thermial/energysupply"

CLIENT_ID = "Pi4-ShutdownTester"
# 1. initialize client
client = paho.Client(client_id=CLIENT_ID, protocol=paho.MQTTv5)
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(HIVEMQ_USER, HIVEMQ_PASS)
# 2. Connect
client.connect(BROKER_HOST_HIVEMQ, BROKER_PORT_HIVEMQ, 60)
client.loop_start()
# 3. Wait, then send command (Payload "1")
time.sleep(2) 
print(f"Send Shutdown-Command '1' an {TOPIC_ENERGY_SUPPLY}")
client.publish(TOPIC_ENERGY_SUPPLY, "1", qos=1)
# 4. Wait and disconnect
time.sleep(1)
client.loop_stop()
client.disconnect()
print("Command send, script finished.")