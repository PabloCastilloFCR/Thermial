#!/usr/bin/env python3
import asyncio
import json
import logging
import paho.mqtt.client as paho
from paho import mqtt
import time
import threading
from datetime import datetime

logger = logging.getLogger("client")        # choose a namespace for your module
handler = logging.StreamHandler()           # print to stdout
fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
handler.setFormatter(logging.Formatter(fmt))
logger.addHandler(handler)

# Toggle verbosity here:
logger.setLevel(logging.INFO) # verbose: WARNING, INFO, DEBUG


valve1_open = asyncio.Event() # async Event
shutdown_event = asyncio.Event()
registration_confirmed = asyncio.Event()
shutdown_confirmed = asyncio.Event()
client = None

TOPIC_RESPONSE = "thermial/register/response"
TOPIC_ENERGY_SUPPLY = "thermial/energysupply" # for energy supply through Raspberry Pi Pico W

#create a logger

TARGET_TANK_TEMP = 45
DEADBAND = 1

HEATER_ON_THRESHOLD = TARGET_TANK_TEMP - DEADBAND
HEATER_OFF_THRESHOLD = TARGET_TANK_TEMP + DEADBAND
#hysterese_running = True

USER_ID = "Ricarda"
user_registered = False

class SensorInfo:
    def __init__(self):
        self.data = {}
sensor_info = SensorInfo()

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("2.) MQTT connected (client) ✓")
        client.subscribe(TOPIC_RESPONSE, qos=1) #Queue is being processed, registration is send now (real time transmission)
        client.subscribe("thermial/status", qos=1)
        client.subscribe("thermial/shutdown/confirm", qos=1)

    else:
        logger.info(f"MQTT connect failed rc = {rc}")
        
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    logger.debug(f"on_subscribe mid={mid}, granted_qos={granted_qos}")

# MQTT Callback
def on_message(client, userdata, msg):
    global user_registered
    if msg.topic == TOPIC_RESPONSE:
    
        try:
            response = json.loads(msg.payload.decode())
            status = response.get("status")
            if status == "ACCEPTED":
                user_registered = True
                asyncio.get_event_loop().call_soon_threadsafe(registration_confirmed.set) # Wait with hysterese until user is registered
                logger.info(f"3.) Registration ACCEPTED for user '{USER_ID}' ✓")
            elif status == "DENIED":
                user_registered = False
                asyncio.get_event_loop().call_soon_threadsafe(registration_confirmed.set)  
                reason = response.get("reason", "Unknown")
                logger.info(f"✗ Registration DENIED: {reason}")  
            elif status == "UNREGISTERED":
                user_registered = False
                asyncio.get_event_loop().call_soon_threadsafe(registration_confirmed.clear)
                logger.info(f"User '{USER_ID}' unregistered")
        except Exception as e:
            logger.error(f"Error processing registration response: {e}")
        return
        
    if msg.topic == "thermial/shutdown/confirm":
        asyncio.get_event_loop().call_soon_threadsafe(shutdown_confirmed.set)
        logger.info("✓ Server confirmed shutdown")
        return

    try:
        data = json.loads(msg.payload.decode())
        sensor_info.data = data  
        # save the whole dictionary
        #logger.debug(json.dumps(data, indent=2))  # shows the whole data structure

        #status = data.get("status")
        valves = data.get("valves", {})
        pump1 = data.get("pump1", {})
        heater1 = data.get("heater1", {})
        heater2 = data.get("heater2", {})
        pump2 = data.get("pump2", {})
        radiator1 = data.get("radiator1", {})

        #logger debug
        logger.debug(f"Status: {data.get('status')}")
        logger.debug(f"Status Valve 1: {valves.get('valve1_state')}")
        logger.debug(f"Power Pump 1: {pump1.get('duty')}")
        logger.debug(f"Flow Pump 1: {pump1.get('flow')}")
        logger.debug(f"Power Heater 1: {heater1.get('duty')}")
        logger.debug(f"Temp Heater 1 In: {heater1.get('temp_in')}")
        logger.debug(f"Temp Heater 1 Out: {heater1.get('temp_out')}")
        logger.debug(f"Power Heater 2: {heater2.get('duty')}")
        logger.debug(f"Temp Heater 2 Out: {heater2.get('temp_out')}")
        logger.debug(f"Power Pump 2: {pump2.get('duty')}")
        logger.debug(f"Flow Pump 2: {pump2.get('flow')}")
        logger.debug(f"Duty Radiator 1: {radiator1.get('duty')}")
        logger.debug(f"Temp Radiator 1 In: {radiator1.get('temp_in')}")
        logger.debug(f"Temp Radiator 1 Out: {radiator1.get('temp_out')}")
        if valves.get("valve1_state") == 1:
            asyncio.get_event_loop().call_soon_threadsafe(valve1_open.set) # set event in order to open valve
            logger.debug("valve opened")
        else:
            asyncio.get_event_loop().call_soon_threadsafe(valve1_open.clear) # reset event in order to close the valve
    except Exception as e:
        logger.error("Error reading the message:", e)

def wait_for_user_cancel():
    """Runs in separate thread, waits for user to type CANCEL"""
    while True:
        user_input = input()
        if user_input.strip().upper() == "CANCEL":
            logger.info("✓ CANCEL command received")
            shutdown_event.set()
            break

# Hysterese
async def hysterese_control():
    global client
    global user_registered

    last_temp = None #last tank temp
    mode = None # three modes: heat, cool, keep
    last_mode = None # only send commands, when mode is switching in order to have no TimeOut Error through message overload
    
    last_cmd = {
        "pump1": 0,
        "heater1": 0,
        "heater2": 0,
        "pump2": 0,
        "radiator1": 0,
        "valve1": 0
    }

    last_error = "None"

    while not shutdown_event.is_set():
        temp_top = sensor_info.data.get("tank", {}).get("temp_top") 
        temp_bottom = sensor_info.data.get("tank", {}).get("temp_bottom") 
        
        # skip loop if no valid temperature available
        if temp_top is None or temp_bottom is None:
            await asyncio.sleep(2)
            continue

        average_temp_tank = (temp_top + temp_bottom) / 2
        
        # start mode, only once after switching on the system in order to see in which temperature range we are in 
        # and SET the corresponding start mode (not execute it), not allow keep, because last cmd = None leads to both pumps 0
        
        if mode is None:
            if average_temp_tank > HEATER_OFF_THRESHOLD:
                mode = "cooling"
                logger.info("start mode = cooling")
            else:
                mode = "heating"
                logger.debug("start mode = heating") #keep not allowed at start


# hysteresis, during operation

        # only change in the mode, no hardware control
        logger.debug(f"temp={average_temp_tank:.2f}, mode={mode}, on_threshold={HEATER_ON_THRESHOLD}, off_threshold={HEATER_OFF_THRESHOLD}")

        if mode == "cooling" and average_temp_tank < HEATER_ON_THRESHOLD:
                logger.debug(f"Switching cooling->heating because {average_temp_tank} < {HEATER_ON_THRESHOLD}")
                mode = "heating"
                logger.debug("switch mode from cooling to heating")

        elif mode == "heating" and average_temp_tank > HEATER_OFF_THRESHOLD:
                logger.debug(f"DEBUG: Switching heating->cooling because {average_temp_tank} > {HEATER_OFF_THRESHOLD}")
                mode = "cooling"
                logger.debug("switch mode from heating to cooling")
            
        elif mode == "keep":
            if average_temp_tank < HEATER_ON_THRESHOLD:
                mode = "heating"
                logger.debug("Keep: heating")
            elif average_temp_tank > HEATER_OFF_THRESHOLD:
                mode = "cooling"  
                logger.debug("Keep: cooling")  

        if average_temp_tank != last_temp:
            logger.info(f"Current tank temperature: {average_temp_tank:.2f}°C")
            last_temp = average_temp_tank

        # hardware commands(orders) ONLY, when mode is switching

        if mode != last_mode:
            logger.info(f"MODE: changed from {last_mode} to {mode}")
            last_mode = mode


             # ========== Sending all commands with user_id ==========
            if mode == "heating":
                client.publish("thermial/valve1/cmd", json.dumps({"user_id": USER_ID, "value": 1}))
                await valve1_open.wait()
                logger.debug("Valve 1 is opened")
                client.publish("thermial/pump1/cmd", json.dumps({"user_id": USER_ID, "value": 100}))
                client.publish("thermial/heater1/cmd", json.dumps({"user_id": USER_ID, "value": 100}))
                client.publish("thermial/heater2/cmd", json.dumps({"user_id": USER_ID, "value": 100}))
                client.publish("thermial/pump2/cmd", json.dumps({"user_id": USER_ID, "value": 0}))
                client.publish("thermial/radiator/cmd", json.dumps({"user_id": USER_ID, "value": 0}))
                client.publish("thermial/valve2/cmd", json.dumps({"user_id": USER_ID, "value": 0}))
                                
                # Update command dictionary
                last_cmd["pump1"] = 100
                last_cmd["heater1"] = 100
                last_cmd["heater2"] = 100
                last_cmd["valve1"] = 1
                last_cmd["pump2"] = 0
                last_cmd["radiator1"] = 0

                logger.debug("Heaters are on")

                # stop heater, start radiator, when average tank temperature is above desired temperature

            elif mode == "cooling":
                #start radiator
                client.publish("thermial/heater1/cmd", json.dumps({"user_id": USER_ID, "value": 0}))
                client.publish("thermial/heater2/cmd", json.dumps({"user_id": USER_ID, "value": 0}))
                client.publish("thermial/pump1/cmd", json.dumps({"user_id": USER_ID, "value": 0}))
                client.publish("thermial/valve1/cmd", json.dumps({"user_id": USER_ID, "value": 0}))
                client.publish("thermial/pump2/cmd", json.dumps({"user_id": USER_ID, "value": 100}))
                client.publish("thermial/radiator/cmd", json.dumps({"user_id": USER_ID, "value": 100}))

                # Update command dictionary
                last_cmd["pump1"] = 0
                last_cmd["heater1"] = 0
                last_cmd["heater2"] = 0
                last_cmd["valve1"] = 0
                last_cmd["pump2"] = 100
                last_cmd["radiator1"] = 100

                logger.debug("Closing Valve and Heaters are OFF because target tank temperature is reached. Radiator is ON.")

            else:
                #keep state
                logger.debug("Keep state, no changes.")

            last_mode = mode # safe current mode

            # Publish controller status

        status_payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hysteresis_low": HEATER_ON_THRESHOLD,
            "hysteresis_high": HEATER_OFF_THRESHOLD,
            "tank_temp": round(average_temp_tank, 2) if average_temp_tank else None,
            "target_temp": TARGET_TANK_TEMP,
            "status": mode if mode else "initializing",
            "pump1_duty": last_cmd.get("pump1", -1),
            "heater1_duty": last_cmd.get("heater1", -1),
            "heater2_duty": last_cmd.get("heater2", -1),
            "pump2_duty": last_cmd.get("pump2", -1),
            "radiator1_duty": last_cmd.get("radiator1", -1),
            "valve1_state": last_cmd.get("valve1", -1),
            "last_update": asyncio.get_event_loop().time(),
            "last_error": last_error,
            "active_user": USER_ID
        }

        client.publish("thermial/controller/status", json.dumps(status_payload), qos = 1, retain = False)
        logger.debug(f"Published controller status: {mode}, Tank: {average_temp_tank}°C")
    
        await asyncio.sleep(30)

    logger.info("Hysteresis control stopped.")

    
# MQTT loop for asyncio
async def mqtt_loop(client):
    while True:
        client.loop_read()
        client.loop_write()
        client.loop_misc()
        await asyncio.sleep(0.005)


async def main():
    global client
    global user_registered
    HIVEMQ_USER = "thermialController"
    HIVEMQ_PASS = "Fcr.2025"
    BROKER_HOST_HIVEMQ = "96916c26427f41a395170e4ee96828c6.s1.eu.hivemq.cloud"
    BROKER_PORT_HIVEMQ = 8883


    client = paho.Client(client_id="thermial_client", protocol=paho.MQTTv5)
    client.enable_logger()
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(HIVEMQ_USER, HIVEMQ_PASS)
    
 
    client.connect(BROKER_HOST_HIVEMQ, 8883) #starts the connecting, non blocking
    
    mqtt_task = asyncio.create_task(mqtt_loop(client))

    # Registration
    time.sleep(1)
    register_msg = {"action": "register", "user_id": USER_ID}
    client.publish("thermial/register", json.dumps(register_msg), qos=1) # puts message in queue
    logger.info(f"1.) Sent registration request for user '{USER_ID}' ✓") # messages appears immediately, connection is created in background

    # Waiting for feedback from user registration
    try:
        await asyncio.wait_for(registration_confirmed.wait(), timeout=5.0)
        if user_registered:
            logger.info("4.) Starting hysteresis control. ✓")

            # ========== Experiment-Start Signal for Node Red in order to create a new Excel ==========
            experiment_start_payload = {
                "command": "start",
                "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                "user_id": USER_ID
            }
            client.publish("experiment/control", json.dumps(experiment_start_payload), qos=1)
            logger.debug(f"✓ Experiment started: {experiment_start_payload['timestamp']}")
            # ==========================================================================================

            hysterese_task = asyncio.create_task(hysterese_control())
        else:
            logger.error("✗ ERROR: Registration was DENIED, because other user is already registered")
            return
    except asyncio.TimeoutError:
        logger.error("✗ ERROR: Registration timeout - no response from server!")
        return
    
    #start thread to wait for user input
    logger.info("5.) System running. Type 'CANCEL' and press ENTER to stop safely. ✓\n")
    input_thread = threading.Thread(target=wait_for_user_cancel, daemon=True)
    input_thread.start()

    # define duration of experiment 
    try:
        await asyncio.wait_for(shutdown_event.wait(), timeout=4*60*60)  # 3 hours in seconds
    except asyncio.TimeoutError:
        logger.info("\n✓ 8 hours elapsed, stopping experiment")
        shutdown_event.set()

    # Wait for Shutdown Signal, when ended with CANCEL, otherwise use duration definition above
    #await shutdown_event.wait()
    #logger.info("\nShutdown initiated.")

    # Stop hysteresis control
    await hysterese_task

    # Send unregister
    if user_registered:
        # =============================================
        #reset dashboard for the gauges in Nodered to start with 0
        reset_payload = {
            "command": "reset_dashboard",
            "userd_id": USER_ID
        }
        client.publish("experiment/control", json.dumps(reset_payload), qos=1)
        await asyncio.sleep(0.5)
        # =============================================
        unregister_msg = {"action": "unregister", "user_id": USER_ID}
        client.publish("thermial/register", json.dumps(unregister_msg), qos=1)

        try:
            await asyncio.wait_for(shutdown_confirmed.wait(), timeout=3.0)
            logger.info("✓ Shutdown confirmed by server")
        except asyncio.TimeoutError:
            logger.warning("⚠ WARNING: No shutdown confirmation from server! Check hardware manually!")

        # *******************************************************************# 
        # Turn off power supply after all current actuators have stopped.        
        client.publish(TOPIC_ENERGY_SUPPLY, "1", qos=1) # <--- send command here (1 = Turn off)        
        logger.info("✓ Sent command to switch OFF external energy supply.") 
        # # *******************************************************************

        
        logger.info(f"✓ Sent unregister request for user '{USER_ID}'")
        

        # Cancel MQTT task
    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        pass

        # Unconnect from MQTT 
       
    client.disconnect()
    logger.info("✓ MQTT disconnected")
    logger.info("✓ Shutdown complete")
    

# ===== Start Event Loop =====
asyncio.run(main())