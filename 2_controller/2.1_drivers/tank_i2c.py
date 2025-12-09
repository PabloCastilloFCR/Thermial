# This module is only a library (API) that provides reusable functions;
# Does not contain code that executes automatically or tests its own functionality
# It has only ONE main dependency: the Tank class, which is the reusable module
# If another program (e.g. main.py) wants to control the tank, imports tank class
# Code within Tank class automatically manages all necessary internal dependencies

import time
from . import i2c_address 
from . import i2c_base   
 
class Tank:
    def __init__(self, device_key="HEAT_STORAGE", verbose=False):
        # Load the address (0x13) from the JSON map
        self.address = i2c_address.load_i2c_address(device_key)
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        self.device_name = "Tank Module"
        self.level = None
        self.temp_bottom = 0.0
        self.temp_top = 0.0
        self.verbose = verbose
        self.tank_height = 40.0 # Height used for level calculation
 
    def get_temperatures(self):
        """Requests and parses the two temperature values (CMD 0x12)."""
        i2c_base.send_command(self.address, 0, 0x02, verbose=self.verbose)
        time.sleep(0.5)
        response_cmd, payload = i2c_base.receive_response(self.address, verbose=self.verbose)
        # Parsing Logic: Check for CMD 0x12 AND LENGTH 4
        if response_cmd == 0x12 and len(payload) == 4:
            self.temp_bottom = (payload[0] | (payload[1] << 8)) / 100.0
            self.temp_top = (payload[2] | (payload[3] << 8)) / 100.0
            if self.verbose:
                print(f"[Tank] Temp: Bottom={self.temp_bottom:.2f}°C, Top={self.temp_top:.2f}°C")
            return self.temp_bottom, self.temp_top
        else:
            return None, None
    def get_level(self):
        """Requests and returns the current level (CMD 0x14)."""
        i2c_base.send_command(self.address, 0, 0x03, verbose=self.verbose)
        time.sleep(0.5) 
        response_cmd, payload = i2c_base.receive_response(self.address, verbose=self.verbose)
 
        # Parsing Logic: Check for CMD 0x14 AND LENGTH 2
        if response_cmd == 0x14 and len(payload) == 2:
            lvl_raw = (payload[0] | (payload[1] << 8))
            measured_distance = lvl_raw / 10.0
            level = max(0.0, self.tank_height - measured_distance)
            self.level = level
            if self.verbose:
                print(f"[Tank] Level: {self.level:.1f} cm (Distance: {measured_distance:.1f} cm)")
            return self.level
        else:
            self.level = -1
            return None