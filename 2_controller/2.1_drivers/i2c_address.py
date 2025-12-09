import json
import os
import sys
 
# --- Path Definition --- 
# This logic is necessary to find the 0_configuration directory from the current file's location.
current_dir = os.path.dirname(os.path.abspath(__file__)) 
controller_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(controller_dir)
 
# Defines the absolute path to the I2C_map.json file
CONFIG_PATH = os.path.join(root_dir, '0_configuration', 'I2C_map.json')
# -----------------------
 
def load_i2c_address(device_key: str) -> int:
    """
    Loads the I2C address for a given device key from I2C_map.json.
    :param device_key: The string key defined in the JSON (e.g., "HEAT_STORAGE").
    :return: The I2C address as an integer (e.g., 19 for 0x13).
    """
    try:
        # 1. Open and load the central configuration file
        with open(CONFIG_PATH, 'r') as f:
            i2c_map = json.load(f)
        # 2. Look up the address string using the provided key
        if device_key in i2c_map:
            address_str = i2c_map[device_key]["address"]
            # 3. Convert the hexadecimal string ('0x13') into an integer (19)
            return int(address_str, 16)
        else:
            raise KeyError(f"'{device_key}' not found in I2C_map.json.")
    except Exception as e:
        print(f"ERROR loading I2C address for {device_key}: {e}")
        return None