# In 2.1_drivers/i2c_address.py
 
import os
import json
def load_i2c_address(device_key: str):
    """
    Dynamically loads the I2C address for a given device key (e.g., 'PUMP1_SOLAR_LOOP').
    This function calculates the path to the central configuration file
    (I2C_map.json) located in the 0_configuration folder.
    """
    # 1. Calculate the absolute path to the I2C_map.json file.
    # Current location: 2.1_drivers/
    # Target location: ../../0_configuration/I2C_map.json
    # Path calculation steps:
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    controller_dir = os.path.dirname(current_dir)  # Up to 2_controller
    base_dir = os.path.dirname(controller_dir)      # Up to Thermial/
    json_path = os.path.join(base_dir, '0_configuration', 'I2C_map.json')
    if not os.path.exists(json_path):
        print(f"[I2C_ADDRESS ERROR] Configuration file not found at: {json_path}")
        return None
    try:
        # 2. Open and load the JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        # 3. Search for the device key in all sections of the map
        for device_group in data.values():
            if device_key in device_group:
                # Convert the address string ("0x10") to an integer (16)
                return int(device_group[device_key], 16) 
    except Exception as e:
        print(f"[I2C_ADDRESS ERROR] Failed to load map or find key '{device_key}': {e}")
        return None
    # 4. Return None if the key was not found
    return None
 
# Optionaler Test, falls die Datei direkt ausgeführt wird
if __name__ == "__main__":
    test_address = load_i2c_address("PUMP1_SOLAR_LOOP")
    print(f"Test Address for PUMP1_SOLAR_LOOP: {hex(test_address) if test_address else None}")