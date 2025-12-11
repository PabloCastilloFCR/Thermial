# This module is only a library (API) that provides reusable functions;
# Does not contain code that executes automatically or tests its own functionality
# It has only ONE main dependency: the Pump class, which is the reusable module
# If another program (e.g. main.py) wants to control the pump, it imports pump class
# Code within Pump class automatically manages all necessary internal dependencies
import time
# Assuming load_i2c_address is available via i2c_base or a dedicated import
from i2c_base import send_command, receive_response, load_i2c_address 
class Pump:
    def __init__(self, device_key="PUMP1_SOLAR_LOOP", verbose=False):
        # Load address 0x10 from JSON map via the key
        self.address = load_i2c_address(device_key)
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
        send_command(self.address, 0, 0x01, [int(power)], verbose=self.verbose)
        self.power = power
    def get_flow(self):
        """
        Requests and parses the current flow value (Response CMD 0x13).
        Uses the GET command (0x02).
        """
        # 1. Send GET command (0x02)
        send_command(self.address, 0, 0x02, verbose=self.verbose)
        time.sleep(0.5)
        # 2. Receive raw data
        response_cmd, payload = receive_response(self.address, verbose=self.verbose)
        # CRITICAL CHECK: Check if receive_response failed (returned None, None)
        if payload is None:
            if self.verbose: print(f"[Pump] I2C read failed for flow on 0x{self.address:02x}.")
            return 0.0 # FIX: Return 0.0 instead of None on I2C communication failure
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
            return -1 # FIX: Return 0.0 if the received data is invalid or wrong CMD