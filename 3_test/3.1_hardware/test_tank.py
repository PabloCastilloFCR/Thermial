# In 3_test/3.1_hardware/test_tank.py
 
import time
import os
import sys
 
# --- Path Definition --- 
# This logic ensures Python can find the '2_controller' package from the '3_test/3.1_hardware' folder.
current_dir = os.path.dirname(os.path.abspath(__file__)) # Gets the path to 3.1_hardware
test_dir = os.path.dirname(current_dir)                   # Moves up to 3_test
root_dir = os.path.dirname(test_dir)                      # Moves up to the project root
 
# [FIX] Append the project root to sys.path so '2_controller' can be found.
sys.path.append(root_dir)
# -----------------------
 
# [FIXED IMPORT] Import the driver class from the new structure
# Note: Python requires the module name '2_controller.2_1_drivers' even though it starts with numbers.
from 2_controller.2_1_drivers.estanque_i2c import Tank
 
if __name__ == "__main__":
    # Create an instance of the Tank class using the JSON key
    tank_module = Tank(device_key="HEAT_STORAGE", verbose=True)
    print(f"--- Starting Tank Test at Address 0x{tank_module.address:02x} ---")
    while True:
        try:
            # GET Temperature test
            tank_module.get_temperatures()
            time.sleep(0.5)
            # GET Level test
            tank_module.get_level()
            time.sleep(0.5)
        except Exception as e:
            print("ERROR in I2C Test Loop:", e)
        time.sleep(5)