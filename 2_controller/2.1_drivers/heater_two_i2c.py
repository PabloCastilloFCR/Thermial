import smbus2
import time
from i2c_address import load_i2c_address

class Heater2:
    def __init__(self, device_key="HEATER2_SOLAR_LOOP", verbose=False):
        self.address = load_i2c_address(device_key)
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        self.device_name = f"Heater 2 ({device_key})"
        self.power = 0
        self.temp_out = 0.0
        self.verbose = verbose

    def _send_i2c_command(self, cmd_id, cmd_code, data=[]):
        """Internal method to send I2C commands using raw i2c_msg."""
        try:
            bus = smbus2.SMBus(1)
            packet = [cmd_id, cmd_code, len(data)] + data
            write = smbus2.i2c_msg.write(self.address, bytes(packet))
            bus.i2c_rdwr(write)
            bus.close()
            if self.verbose:
                print(f"[I2C {self.device_name}] Sent: ADD={self.address:02x}, CMD={cmd_code:02x}, DATA={data}")
            return True
        except Exception as e:
            if self.verbose:
                print(f"[I2C {self.device_name}] Send Error: {e}")
            return False

    def _receive_i2c_response(self, read_len=5):
        """Internal method to receive I2C response using raw i2c_msg."""
        try:
            bus = smbus2.SMBus(1)
            read = smbus2.i2c_msg.read(self.address, read_len)
            bus.i2c_rdwr(read)
            data = list(read)
            bus.close()
            
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

    def set_pwm_heater2(self, pwm_value):
        """Sets the heater PWM (0–100%)."""
        if not 0 <= pwm_value <= 100:
            raise ValueError("PWM must be between 0 and 100")
            
        self._send_i2c_command(0, 0x01, [int(pwm_value)])
        time.sleep(0.1)
        self.power = pwm_value

    def get_temperatures(self):
        """Requests and returns the temperature sensor value."""
        self._send_i2c_command(0, 0x02)
        time.sleep(0.5)
        
        response = self._receive_i2c_response(read_len=5)
        if response:
            cmd, payload = response
            if cmd == 0x12 and len(payload) >= 2:
                self.temp_out = (payload[0] + (payload[1] << 8)) / 100.0
                if self.verbose:
                    print(f"[I2C {self.device_name}] Temp Out: {self.temp_out:.2f}°C")
            else:
                self.temp_out = 0.0
        else:
            self.temp_out = 0.0
            
        return self.temp_out