import time
import os
import sys
 
# --- Path Definition --- 
# Calculating the absolute path to the driver folder (2.1_drivers)

current_dir = os.path.dirname(os.path.abspath(__file__)) 
logic_dir = os.path.dirname(current_dir) #goes to 2_controller
drivers_path = os.path.join(logic_dir, '2.1_drivers')
sys.path.append(drivers_path)

# -----------------------
 
# Importing the driver class

from pumps_i2c import Pump
 
if __name__ == "__main__":
    # Create an instance of the Pump class using the JSON key for Pump 2
    pump_module = Pump(device_key="PUMP2_PROCESS_LOOP", verbose=True)
    print(f"--- Starting Pump 2 Test at Address 0x{pump_module.address:02x} ---")
    # Original test parameters for Pump 2
    value = 90
    increment = 5
    try:
        # Initial SET command
        pump_module.set_power(value)
        while True:
            time.sleep(2)
            # 1. Get flow reading
            flow_value = pump_module.get_flow() 
            # 2. Update power value (Original ramp logic: range 85-100)
            value += increment
            if value > 100 or value < 85: 
                increment = -increment
                value += increment
            # 3. Send new power value
            pump_module.set_power(value)
            time.sleep(0.5)      

    except KeyboardInterrupt:
        print("Stopping Pump 2")
        time.sleep(1)
        pump_module.set_power(0)
        print("Pump 2 OFF.")
 