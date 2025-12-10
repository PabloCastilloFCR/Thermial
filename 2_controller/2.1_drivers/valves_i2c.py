import time
from i2c_address import load_i2c_address 
from i2c_base import send_command, receive_response   
from typing import Tuple, Optional
import smbus2 # Added smbus2 for direct read in get_flows_and_status

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
    def get_flows_and_status(self) -> Tuple[Optional[float], Optional[float], Optional[bool], Optional[bool]]:
        """
        Requests and returns the flow values and current status of both valves.
        """
        send_command(self.address, 0, 0x02, verbose=self.verbose)
        time.sleep(0.5)
        # NOTE: Using direct smbus read due to non-standard header parsing in original code.
        try:
            bus = smbus2.SMBus(1)
            raw = bus.read_i2c_block_data(self.address, 0x00, 7) # Expecting 7 bytes total
            bus.close()
        except Exception as e:
            if self.verbose: print(f"[Valves] Error reading response: {e}")
            return None, None, None, None
        # Original 0x12 parsing logic (CMD at [0], LEN at [1])
        response_cmd = raw[0]
        response_len = raw[1]
        response_data = raw[2:2+response_len]
 
        # 3. Parsing Logic: Check for Response CMD 0x13 and minimum LENGTH 5
        if response_cmd == 0x13 and len(response_data) >= 5:
            self.flow_valve1_out = (response_data[0] | (response_data[1] << 8)) / 100.0
            self.flow_valve2_out = (response_data[2] | (response_data[3] << 8)) / 100.0
            valve_status_byte = response_data[4]
            # Extract status flags
            self.state_valve1 = bool(valve_status_byte & 0x01)
            self.state_valve2 = bool(valve_status_byte & 0x02)
            if self.verbose:
                print(f"[Valves] Flow 1: {self.flow_valve1_out:.2f} L/min, Flow 2: {self.flow_valve2_out:.2f} L/min")
                print(f"[Valves] Status: V1 {'OPEN' if self.state_valve1 else 'CLOSED'}, V2 {'OPEN' if self.state_valve2 else 'CLOSED'}")
 
            return self.flow_valve1_out, self.flow_valve2_out, self.state_valve1, self.state_valve2
        else:
            if self.verbose: print(f"[Valves] Error: Unexpected response format (CMD {response_cmd:02x}, LEN {response_len}).")
            return None, None, None, None