import time
from typing import Tuple, Optional
# FIX 1: Complete the import from i2c_base
from i2c_base import send_command, receive_response, load_i2c_address 
# FIX 2: smbus2 is no longer needed here, as receive_response handles it
# import smbus2 
# Logic for opening / closing the valves 1 and 2:
# V1 Close -> [1] | V2 Close -> [2]
# V1 Open -> [3]  | V2 Open -> [4]
CLOSE_V1 = [1]
CLOSE_V2 = [2]
OPEN_V1 = [3]
OPEN_V2 = [4]
# ---------------------------------------------------------
class Valve:
    def __init__(self, device_key="VALVES", verbose=False):
        self.address = load_i2c_address(device_key)
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        self.device_name = "Valves and Flowmeters Module"
        self.flow_valve1_out = 0.0
        self.flow_valve2_out = 0.0
        self.state_valve1 = None
        self.state_valve2 = None
        self.verbose = verbose
    # --- SET Commands ---
    def set_valve_state(self, valve_num: int, state: bool):
        """
        Sets the state of a specific valve (True=Open, False=Closed).
        """
        if valve_num == 1:
            data = OPEN_V1 if state else CLOSE_V1
            self.state_valve1 = state
        elif valve_num == 2:
            data = OPEN_V2 if state else CLOSE_V2
            self.state_valve2 = state
        else:
            raise ValueError("Valve number must be 1 or 2.")
        # Command format: ID=0, CMD=0x01, Data=[1/2/3/4]
        send_command(self.address, 0, 0x01, data, verbose=self.verbose)
        time.sleep(0.1)
    def open_valve(self, valve_num: int):
        """Opens a specific valve."""
        self.set_valve_state(valve_num, True)
    def close_valve(self, valve_num: int):
        """Closes a specific valve."""
        self.set_valve_state(valve_num, False)
    # --- GET Command and Parsing ---
    def get_flows_and_status(self) -> Tuple[float, float, bool, bool]: # Changed return type to avoid Optional for defaults
        """
        Requests and returns the flow values and current status of both valves.
        FIX: Uses receive_response() instead of direct smbus read.
        """
        send_command(self.address, 0, 0x02, verbose=self.verbose)
        time.sleep(0.5)
        # FIX 3: Use central receive_response instead of manual try/except smbus read
        response_cmd, payload = receive_response(self.address, verbose=self.verbose)
        # FIX 4: Check for I2C read failure (payload is None)
        if payload is None:
            if self.verbose: print(f"[Valves] I2C read failed. Returning defaults.")
            # Return safe default values (0.0 for flow, False for state) on failure
            return 0.0, 0.0, False, False
        # NOTE: Your old code assumed non-standard header parsing (CMD at [0], LEN at [1]),
        # but the new i2c_base.py uses the standard (ID at [0], CMD at [1], LEN at [2]).
        # The logic below relies on the standard parsing from i2c_base.py.
        # 3. Parsing Logic: Check for Response CMD 0x13 and minimum LENGTH 5
        if response_cmd == 0x13 and len(payload) >= 5:
            # FIX 5: Data decoding (Byte shift and scaling)
            self.flow_valve1_out = (payload[0] | (payload[1] << 8)) / 100.0
            self.flow_valve2_out = (payload[2] | (payload[3] << 8)) / 100.0
            valve_status_byte = payload[4]
            # Extract status flags
            self.state_valve1 = bool(valve_status_byte & 0x01)
            self.state_valve2 = bool(valve_status_byte & 0x02)
            if self.verbose:
                print(f"[Valves] Flow 1: {self.flow_valve1_out:.2f} L/min, Flow 2: {self.flow_valve2_out:.2f} L/min")
                print(f"[Valves] Status: V1 {'OPEN' if self.state_valve1 else 'CLOSED'}, V2 {'OPEN' if self.state_valve2 else 'CLOSED'}")
            return self.flow_valve1_out, self.flow_valve2_out, self.state_valve1, self.state_valve2
        else:
            if self.verbose: print(f"[Valves] Error: Unexpected response format (CMD {response_cmd:02x}, LEN {len(payload)}).")
            # FIX 6: Return safe default values on parsing error
            return 0.0, 0.0, False, False