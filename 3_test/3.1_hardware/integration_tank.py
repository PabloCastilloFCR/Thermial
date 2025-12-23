# In 3_test/3.1_hardware/test_tank.py
 
import time
import os
import sys
 
# --- Path Definition --- 
current_dir = os.path.dirname(os.path.abspath(__file__)) 
thermial_root = os.path.dirname(os.path.dirname(current_dir)) # goes to root (Thermial)
drivers_path = os.path.join(thermial_root, '2_controller', '2.1_drivers')
sys.path.append(drivers_path)
# -----------------------
 
# Import the driver class from the new structure
from tank_i2c import Tank
 
if __name__ == "__main__":
    # Create an instance of the Tank class using the JSON key
    tank_module = Tank(device_key="HEAT_STORAGE", verbose=True)
    print(f"--- Starting Tank Test at Address 0x{tank_module.address:02x} ---")
    while True:
        try:
            # GET Temperature test (Calls logic inside estanque_i2c.py)
            tank_module.get_temperatures()
            time.sleep(0.5)
            # GET Level test (Calls logic inside estanque_i2c.py)
            tank_module.get_level()
            time.sleep(0.5)
        except Exception as e:
            print("ERROR in I2C Test Loop:", e)
        time.sleep(5)