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
from heaters_i2c import Heater
 
if __name__ == "__main__":
    # Create an instance of the Heater class using the JSON key for Heater 2
    heater_module = Heater(device_key="HEATER2_SOLAR_LOOP", verbose=True)
    print(f"--- Starting Heater 2 Test at Address 0x{heater_module.address:02x} ---")
    # Test parameters (Original ramp logic from 0x16)
    value = 0 
    increment = 10 
    try:
        while True:
            # 1. Request and get temperature (Returns Temp Out only)
            temp_out = heater_module.get_temperatures() 
            time.sleep(0.5)
            # 2. Optional: Request and get current PWM value
            heater_module.get_pwm()
            time.sleep(0.5)
            # 3. Send new PWM order (SET)
            heater_module.set_pwm(value)
            time.sleep(1)
            # 4. Increment or decrease PWM value
            value += increment
            if value > 100 or value < 0:
                increment = -increment
                value += increment
    except KeyboardInterrupt:
        print("Stopping Heater 2")
        heater_module.set_pwm(0)
        print("Heater 2 OFF.")