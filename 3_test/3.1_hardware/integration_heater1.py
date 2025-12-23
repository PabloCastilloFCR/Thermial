import time
import os
import sys
 
# --- Path Definition --- 
current_dir = os.path.dirname(os.path.abspath(__file__)) 
thermial_root = os.path.dirname(os.path.dirname(current_dir)) # goes to root (Thermial)
drivers_path = os.path.join(thermial_root, '2_controller', '2.1_drivers')
sys.path.append(drivers_path)
# -----------------------
 
# Importing the driver class
from heater_i2c import Heater1 as Heater
 
if __name__ == "__main__":
    heater_module = Heater(device_key="HEATER1_SOLAR_LOOP", verbose=True) 
    print(f"--- Starting Heater 1 Test at Address 0x{heater_module.address:02x} ---")
    # Original test parameters
    value = 0 
    increment = 10 
    try:
        while True:
            # 1. Request and get temperatures (Returns In and Out temps)
            temp_in, temp_out = heater_module.get_temperatures() 
            time.sleep(0.5)
            # 2. Send new PWM order (SET)
            heater_module.set_pwm_heater1(value)
            time.sleep(1)
            # 4. Increment or decrease PWM value
            value += increment
            if value > 100 or value < 0:
                increment = -increment
                value += increment
    except KeyboardInterrupt:
        print("Stopping Heater 1")
        heater_module.set_pwm_heater1(0)
        print("Heater 1 OFF.")