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
from radiator_i2c import Radiator
 
if __name__ == "__main__":
    # Create an instance of the Radiator class using the JSON key
    radiator_module = Radiator(device_key="RADIATOR_PROCESS_LOOP", verbose=True)
    print(f"--- Starting Radiator Test at Address 0x{radiator_module.address:02x} ---")
    # Original test parameters (ramp logic from 0x15)
    value = 70 
    increment = 5 
    try:
        while True:
            # 1. Request and get temperatures 
            radiator_module.get_temperatures() 
            time.sleep(0.5)
            # 2. Optional: Request and get current PWM value
            radiator_module.get_pwm()
            time.sleep(0.5)
            # 3. Send new PWM order (SET)
            radiator_module.set_pwm(value)
            time.sleep(1)
            # 4. Increment or decrease PWM value
            value += increment
            if value > 100 or value < 70:
                increment = -increment
                value += increment
    except KeyboardInterrupt:
        print("Stopping Radiator Fan")
        radiator_module.set_pwm(0)
        print("Radiator Fan OFF.")