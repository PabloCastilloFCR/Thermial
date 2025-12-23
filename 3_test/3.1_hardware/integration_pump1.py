import time
import os
import sys
 
# --- Path Definition --- 
current_dir = os.path.dirname(os.path.abspath(__file__)) 
thermial_root = os.path.dirname(os.path.dirname(current_dir)) # goes to root (Thermial)
drivers_path = os.path.join(thermial_root, '2_controller', '2.1_drivers')
sys.path.append(drivers_path)
# -----------------------
 
# Importing the driver using the module name pump_i2c
from pumps_i2c import Pump
 
if __name__ == "__main__":
    # Create an instance of the Pump class using the JSON key
    pump_module = Pump(device_key="PUMP1_SOLAR_LOOP", verbose=True)
    print(f"--- Starting Pump Test at Address 0x{pump_module.address:02x} ---")
    # Original test parameters
    value = 90
    increment = 5
    try:
        pump_module.set_power(value)
        while True:
            time.sleep(2)
            # 1. Get flow reading
            flow_value = pump_module.get_flow() 
            # 2. Update power value (Original ramp logic)
            value += increment
            if value > 100 or value < 70: 
                increment = -increment
                value += increment
            # 3. Send new power value
            pump_module.set_power(value)
            time.sleep(0.5)
 
            
    except KeyboardInterrupt:
        print("Stopping Pump")
        time.sleep(1)
        pump_module.set_power(0)
        print("Pump OFF.")