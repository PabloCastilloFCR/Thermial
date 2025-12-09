import time
import os
import sys
 
# --- Path Definition --- 
# Calculating the absolute path to the driver folder (2.1_drivers)
current_dir = os.path.dirname(os.path.abspath(__file__)) 
test_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(test_dir)
drivers_path = os.path.join(root_dir, '2_controller', '2.1_drivers')
sys.path.append(drivers_path)
# -----------------------
 
# Importing the driver class
from heater1_i2c import Heater1
 
if __name__ == "__main__":
    # Create an instance of the Heater1 class using the JSON key
    heater_module = Heater1(device_key="HEATER1_SOLAR_LOOP", verbose=True)
    print(f"--- Starting Heater 1 Test at Address 0x{heater_module.address:02x} ---")
    # Original test parameters
    value = 0 # PWM for heater (0-100%)
    increment = 10 # PWM step size
    try:
        while True:
            # 1. Request and get temperatures (Calls logic inside heater1_i2c.py)
            heater_module.get_temperatures() 
            time.sleep(0.5)
            # 2. Optional: Request and get current PWM value
            heater_module.get_pwm()
            time.sleep(0.5)
            # 3. Send new PWM order (SET)
            heater_module.set_pwm(value)
            time.sleep(1)
            # 4. Increment or decrease PWM value (Original ramp logic)
            value += increment
            if value > 100 or value < 0:
                increment = -increment
                value += increment
    except KeyboardInterrupt:
        print("Stopping Heater 1")
        heater_module.set_pwm(0)
        print("Heater 1 OFF.")