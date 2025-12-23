import smbus2
import time
from i2c_address import load_i2c_address 

class Valves:
    def __init__(self, device_key="VALVES", verbose=False):
        self.address = load_i2c_address(device_key) 
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        self.device_name = f"Valves ({device_key})"
        self.flow_valve1_out = 0.0
        self.flow_valve2_out = 0.0
        self.state_valve1 = None
        self.state_valve2 = None
        self.verbose = verbose

    def _send_i2c_command(self, cmd_id, cmd_code, data=[]):
        """Internal method to send I2C commands using SMBus block protocol."""
        try:
            bus = smbus2.SMBus(1)
            packet = [cmd_id, cmd_code, len(data)] + data
            bus.write_i2c_block_data(self.address, 0x00, packet)
            bus.close()
            time.sleep(0.05) # Small delay for bus stability
            if self.verbose:
                print(f"[I2C {self.device_name}] Sent: ADD={self.address:02x}, CMD={cmd_code:02x}, DATA={data}")
            return True
        except Exception as e:
            if self.verbose:
                print(f"[I2C {self.device_name}] Send Error: {e}")
            return False

    def _receive_i2c_response(self, read_len=7):
        """Internal method to receive I2C response using SMBus block protocol."""
        try:
            bus = smbus2.SMBus(1)
            data = bus.read_i2c_block_data(self.address, 0x00, read_len)
            bus.close()
            
            if len(data) < 2:
                return None
            
            # Note: Module 0x12 returns [CMD, LEN, DATA...] without ID byte
            resp_cmd = data[0]
            resp_len = data[1]
            resp_payload = data[2:2+resp_len]
            
            return resp_cmd, resp_payload
        except Exception as e:
            if self.verbose:
                print(f"[I2C {self.device_name}] Receive Error: {e}")
            return None

    def open_valve(self, numero):
        """Opens a specific valve (1 or 2)."""
        if numero == 1:
            self._send_i2c_command(0, 0x01, [3])
            self.state_valve1 = True
        elif numero == 2:
            self._send_i2c_command(0, 0x01, [4])
            self.state_valve2 = True
        else:
            raise ValueError("Valve number must be 1 or 2")

    def close_valve(self, numero):
        """Closes a specific valve (1 or 2)."""
        if numero == 1:
            self._send_i2c_command(0, 0x01, [1])
            self.state_valve1 = False
        elif numero == 2:
            self._send_i2c_command(0, 0x01, [2])
            self.state_valve2 = False
        else:
            raise ValueError("Valve number must be 1 or 2")

    def get_flows(self):
        """Requests and returns the two flowmeter values and valve states."""
        self._send_i2c_command(0, 0x02)
        time.sleep(0.5)
        
        response = self._receive_i2c_response(read_len=7)
        if response:
            cmd, payload = response
            if cmd == 0x13 and len(payload) >= 5:
                self.flow_valve1_out = (payload[0] + (payload[1] << 8)) / 100.0
                self.flow_valve2_out = (payload[2] + (payload[3] << 8)) / 100.0
                valve_status = payload[4]
                self.state_valve1 = bool(valve_status & 0x01)
                self.state_valve2 = bool(valve_status & 0x02)
                if self.verbose:
                    print(f"[I2C {self.device_name}] Flow1={self.flow_valve1_out:.2f}, Flow2={self.flow_valve2_out:.2f}")
            else:
                self.flow_valve1_out = 0.0
                self.flow_valve2_out = 0.0
        else:
            self.flow_valve1_out = 0.0
            self.flow_valve2_out = 0.0
            
        return self.flow_valve1_out, self.flow_valve2_out
