# This module is only a library (API) that provides reusable functions;
# Does not contain code that executes automatically or tests its own functionality
# It has only ONE main dependency: the Pump class, which is the reusable module
# If another program (e.g. main.py) wants to control the pump, it imports pump class
# Code within Pump class automatically manages all necessary internal dependencies

import time
from . import i2c_address 
from . import i2c_base   
 
class Pump:
    def __init__(self, device_key="PUMP1_SOLAR_LOOP", verbose=False):
        # Load address 0x10 from JSON map via the key
        self.address = i2c_address.load_i2c_address(device_key)
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        self.device_name = "Pump 1 Flowmeter Module"
        self.power = 0
        self.flow = 0.0
        self.verbose = verbose
 
    def set_power(self, power: int):
        """
        Sets the PWM power for the pump (0-100%). Uses the SET command (0x01).
        """
        if not 0 <= power <= 100:
            raise ValueError("Power must be between 0 and 100")
 
        # Command format: ID=0, CMD=0x01, Data=[power]
        i2c_base.send_command(self.address, 0, 0x01, [int(power)], verbose=self.verbose)
        self.power = power
 
    def get_flow(self):
        """
        Requests and parses the current flow value (Response CMD 0x13).
        Uses the GET command (0x02).
        """
        # 1. Send GET command (0x02)
        i2c_base.send_command(self.address, 0, 0x02, verbose=self.verbose)
        time.sleep(0.1) 
        # 2. Receive raw data
        response_cmd, payload = i2c_base.receive_response(self.address, verbose=self.verbose)
        # 3. Parsing Logic: Check for Response CMD 0x13 and LENGTH 2
        if response_cmd == 0x13 and len(payload) == 2:
            # Combine two bytes and scale by 100.0 (Original I2C logic)
            flow_raw = payload[0] + (payload[1] << 8) 
            self.flow = flow_raw / 100.0 
            if self.verbose:
                print(f"[Pump] Flow received: {self.flow:.2f}")
            return self.flow
        else:
            if self.verbose: print(f"[Pump] Unexpected response for Flow (CMD {response_cmd:02x}).")
            return None