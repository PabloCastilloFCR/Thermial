import smbus2
import time
from i2c_address import load_i2c_address 

class Pump:
    def __init__(self, device_key="PUMP1_SOLAR_LOOP", verbose=False):
        # Dynamically fetch the address (0x10 or 0x14)
        self.address = load_i2c_address(device_key) 
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        self.device_name = f"Pump ({device_key})"
        self.power = 0
        self.flow = 0.0
        self.verbose = verbose

    def _send_i2c_command(self, cmd_id, cmd_code, data=[]):
        """Internal method to send I2C commands."""
        try:
            bus = smbus2.SMBus(1)
            packet = [cmd_id, cmd_code, len(data)] + data
            bus.write_i2c_block_data(self.address, 0x00, packet)
            bus.close()
            if self.verbose:
                print(f"[I2C {self.device_name}] Sent: ADD={self.address:02x}, CMD={cmd_code:02x}, DATA={data}")
            return True
        except Exception as e:
            if self.verbose:
                print(f"[I2C {self.device_name}] Send Error: {e}")
            return False

    def _receive_i2c_response(self, read_len=5):
        """Internal method to receive I2C response."""
        try:
            bus = smbus2.SMBus(1)
            data = bus.read_i2c_block_data(self.address, 0x00, read_len)
            bus.close()
            if self.verbose:
                print(f"[I2C {self.device_name}] Raw Received: {data}")
            
            # Basic protocol check: [ID, CMD, LEN, DATA...]
            if len(data) < 3:
                return None
                
            resp_cmd = data[1]
            resp_len = data[2]
            resp_payload = data[3:3+resp_len]
            
            return resp_cmd, resp_payload
        except Exception as e:
            if self.verbose:
                print(f"[I2C {self.device_name}] Receive Error: {e}")
            return None

    def set_power(self, power: int):
        """Sets the pump power (0-100)."""
        if not 0 <= power <= 100:
            raise ValueError("Power must be between 0 and 100")
        
        self._send_i2c_command(0, 0x01, [int(power)])
        self.power = power

    def get_flow(self):
        """Requests and returns the current pump flow."""
        # Send GET command
        self._send_i2c_command(0, 0x02)
        time.sleep(0.5) 
        
        response = self._receive_i2c_response(read_len=5)
        if response:
            cmd, payload = response
            if cmd == 0x13 and len(payload) >= 2: # FLOW command response
                flow_raw = payload[0] + (payload[1] << 8)
                self.flow = flow_raw / 100.0
                if self.verbose:
                    print(f"[I2C {self.device_name}] Flow: {self.flow:.2f} L/min")
            else:
                self.flow = 0.0
        else:
            self.flow = 0.0
            
        return self.flow
