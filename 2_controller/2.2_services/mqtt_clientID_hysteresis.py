#!/usr/bin/env python3
import asyncio
import json
import paho.mqtt.client as mqtt
import time
import threading
from datetime import datetime

valve1_open = asyncio.Event() # async Event
shutdown_event = asyncio.Event()
client = None

#crear un logger

heater_on_threshold = 35
heater_off_threshold = 40
#heaters_are_on = True
hysterese_running = True

USER_ID = "Ricarda"
user_registered = False

class SensorInfo:
    def __init__(self):
        self.data = {}
sensor_info = SensorInfo()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected (client)")
        client.subscribe("thermial/status")
        client.subscribe("thermial/register/response")
    else:
        print(f"MQTT connect failed rc = {rc}")

# MQTT Callback
def on_message(client, userdata, msg):
    global user_registered
    if msg.topic == "thermial/register/response":
    
        try:
            response = json.loads(msg.payload.decode())
            status = response.get("status")
            if status == "ACCEPTED":
                user_registered = True
                print(f"✓ Registration ACCEPTED for user '{USER_ID}'")
            elif status == "DENIED":
                user_registered = False
                reason = response.get("reason", "Unknown")
                print(f"✗ Registration DENIED: {reason}")
            elif status == "UNREGISTERED":
                user_registered = False
                print(f"User '{USER_ID}' unregistered")
        except Exception as e:
            print(f"Error processing registration response: {e}")
        return

    try:
        data = json.loads(msg.payload.decode())
        sensor_info.data = data  
        # save the whole dictionary
        #print(json.dumps(data, indent=2))  # shows the whole data structure

        #status = data.get("status")
        valves = data.get("valves", {})
        pump1 = data.get("pump1", {})
        heater1 = data.get("heater1", {})
        heater2 = data.get("heater2", {})
        pump2 = data.get("pump2", {})
        radiator1 = data.get("radiator1", {})

        #logger debug
        print(f"Status: {data.get('status')}")
        print(f"Status Valve 1: {valves.get('valve1_state')}")
        print(f"Power Pump 1: {pump1.get('duty')}")
        print(f"Flow Pump 1: {pump1.get('flow')}")
        print(f"Power Heater 1: {heater1.get('duty')}")
        print(f"Temp Heater 1 In: {heater1.get('temp_in')}")
        print(f"Temp Heater 1 Out: {heater1.get('temp_out')}")
        print(f"Power Heater 2: {heater2.get('duty')}")
        print(f"Temp Heater 2 Out: {heater2.get('temp_out')}")
        print(f"Power Pump 2: {pump2.get('duty')}")
        print(f"Flow Pump 2: {pump2.get('flow')}")
        print(f"Duty Radiator 1: {radiator1.get('duty')}")
        print(f"Temp Radiator 1 In: {radiator1.get('temp_in')}")
        print(f"Temp Radiator 1 Out: {radiator1.get('temp_out')}")
        if valves.get("valve1_state") == 1:
            asyncio.get_event_loop().call_soon_threadsafe(valve1_open.set) # set event in order to open valve
            print("valve opened")
        else:
            asyncio.get_event_loop().call_soon_threadsafe(valve1_open.clear) # reset event in order to close the valve
    except Exception as e:
        print("Error reading the message:", e)

def wait_for_user_cancel():
    """Runs in separate thread, waits for user to type CANCEL"""
    while True:
        user_input = input()
        if user_input.strip().upper() == "CANCEL":
            print("\n✓ CANCEL command received")
            shutdown_event.set()
            break

# Hysterese
async def hysterese_control():
    global client
    global user_registered

    # Warte bis Registrierung erfolgreich ist
    print("Waiting for user registration...")
    while not user_registered:
        await asyncio.sleep(1)
    print("User registered, starting hysteresis control")
    # =========================================================

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
        # and SET the corresponding start mode (not execute it)
        #if mode is None:
        #    if average_temp_tank > 27:
        #        mode = "cooling"
        #        print("start mode = cooling")

        #    elif average_temp_tank < 26.1:
        #        mode = "heating"
        #        print("start mode = heating")

        #    else:
        #        mode = "keep"
        #        print("start mode = keep (between 26.1-27°C)")

        # start mode, only once after switching on the system in order to see in which temperature range we are in 
        # and SET the corresponding start mode (not execute it), not allow keep, because last cmd = None leads to both pumps 0
        
        if mode is None:
            if average_temp_tank > heater_off_threshold:
                mode = "cooling"
                print("start mode = cooling")
            else:
                mode = "heating"
                print("start mode = heating (keep not allowed at startup)")


# hysteresis, during operation

        # only change in the mode, no hardware control

        if mode == "cooling" and average_temp_tank < 35:
                mode = "heating"
                print("switch mode from cooling to heating")

        elif mode == "heating" and average_temp_tank > 40:
                mode = "cooling"
                print("switch mode from heating to cooling")
            
        elif mode == "keep":
            if average_temp_tank < 35:
                mode = "heating"
                print("Keep: heating")
            elif average_temp_tank > 40:
                mode = "cooling"  
                print("Keep: cooling")  

        if average_temp_tank != last_temp:
            print(f"Current tank temperature: {average_temp_tank}")
            last_temp = average_temp_tank

        # hardware commands(orders) ONLY, when mode is switching

        if mode != last_mode:
            print(f"Mode changed from {last_mode} to {mode}, sending commands")
            last_mode = mode


             # ========== ÄNDERUNG 4: Alle Befehle mit user_id senden ==========
            if mode == "heating":
                client.publish("thermial/valve1/cmd", json.dumps({"user_id": USER_ID, "value": 1}))
                await valve1_open.wait()
                print("Valve 1 is opened")
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

                print("Heaters are on")

                # stop heater, start radiator, when temperature above desired temperature

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

                print("Closing Valve and Heaters are OFF because target temperature is reached. Radiator is ON.")

            else:
                #keep state
                print("Keep state, no changes.")

            last_mode = mode # safe current mode

            # Publish controller status

        status_payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hysteresis_low": heater_on_threshold,
            "hysteresis_high": heater_off_threshold,
            "tank_temp": round(average_temp_tank, 2) if average_temp_tank else None,
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
        print(f"Published controller status: {mode}, Tank: {average_temp_tank}°C")
    
        await asyncio.sleep(30)

    print("Hysteresis control stopped.")

# MQTT loop for asyncio
async def mqtt_loop(client):
    while True:
        client.loop_read()
        client.loop_write()
        client.loop_misc()
        await asyncio.sleep(0.01)


async def main():
    global client
    global user_registered
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("192.168.2.35", 1883, 60)
    client.subscribe("thermial/status")
    client.subscribe("thermial/register/response")

    mqtt_task = asyncio.create_task(mqtt_loop(client))
    hysterese_task = asyncio.create_task(hysterese_control())

    # Registrierung
    register_msg = {"action": "register", "user_id": USER_ID}
    client.publish("thermial/register", json.dumps(register_msg), qos=1)
    print(f"Sent registration request for user '{USER_ID}'")

    #start thread to wait for user input
    print("\nSystem running. Type 'CANCEL' and press ENTER to stop safely.\n")
    input_thread = threading.Thread(target=wait_for_user_cancel, daemon=True)
    input_thread.start()

    # Wait for Shutdown Signal
    await shutdown_event.wait()
    print("\nShutdown initiated.")

    # Stop hysteresis control
    await hysterese_task

    # Send unregister
    if user_registered:
        unregister_msg = {"action": "unregister", "user_id": USER_ID}
        client.publish("thermial/register", json.dumps(unregister_msg), qos=1)
        await asyncio.sleep(1)
        print(f"✓ Sent unregister request for user '{USER_ID}'")
            

        # 4. Cancel MQTT task
    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        pass

        # 2. Unconnect
       
    client.disconnect()
    print("✓ MQTT disconnected")
    print("✓ Shutdown complete")
    

# ===== Event Loop starten =====
asyncio.run(main())