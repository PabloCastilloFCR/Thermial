# In 2.1_drivers/i2c_address.py
 
import os
import json
def load_i2c_address(device_key: str):
    """
    Dynamically loads the I2C address for a given device key.
    (Logic corrected for flat JSON structure in I2C_map.json).
    """
    # 1. Calculate the absolute path (This part is correct)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    controller_dir = os.path.dirname(current_dir)
    base_dir = os.path.dirname(controller_dir)
    json_path = os.path.join(base_dir, '0_configuration', 'I2C_map.json')
    if not os.path.exists(json_path):
        print(f"[I2C_ADDRESS ERROR] Configuration file not found at: {json_path}")
        return None
    try:
        # 2. Open and load the JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        # 3. KORRIGIERTE LOGIK: Schlüssel liegt direkt auf der obersten Ebene
        if device_key in data:
            # Greift auf den inneren "address"-Wert zu (z.B. data["PUMP1_SOLAR_LOOP"]["address"])
            address_hex = data[device_key]["address"]
            # Gibt die Adresse als Integer zurück
            return int(address_hex, 16) 
    except Exception as e:
        # Fängt Fehler beim Dateizugriff oder Parsing ab
        print(f"[I2C_ADDRESS ERROR] Failed to load map or parse key '{device_key}': {e}")
        return None
    # 4. Return None if the key was not found or an error occurred
    return None
 
# Optionaler Test (beibehalten)
if __name__ == "__main__":
    test_address = load_i2c_address("PUMP1_SOLAR_LOOP")
    print(f"Test Address for PUMP1_SOLAR_LOOP: {hex(test_address) if test_address else None}")