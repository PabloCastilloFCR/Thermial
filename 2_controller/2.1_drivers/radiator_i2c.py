import time
from . import i2c_address 
from . import i2c_base   
from typing import Tuple, Optional
 
class Radiator:
    def __init__(self, device_key="RADIATOR_PROCESS_LOOP", verbose=False):
        # Load address 0x15 from JSON map via the key
        self.address = i2c_address.load_i2c_address(device_key)
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        self.device_name = "Radiator Fan Module"
        self.power = 0
        self.temp_in = 0.0
        self.temp_out = 0.0
        self.verbose = verbose
 
    def set_pwm(self, pwm_value: int):
        """
        Sets the PWM value for the fan (0-100%). Uses SET command (0x01).
        """
        if not 0 <= pwm_value <= 100:
            raise ValueError("PWM must be between 0 and 100")
        i2c_base.send_command(self.address, 0, 0x01, [int(pwm_value)], verbose=self.verbose)
        time.sleep(0.1)
        self.power = pwm_value

    def get_pwm(self):
        """
        Requests and parses the current fan PWM value (Response CMD 0x15).
        """
        i2c_base.send_command(self.address, 0, 0x01, verbose=self.verbose) # Command 0x01 for GET PWM status
        time.sleep(0.5) 
        response_cmd, payload = i2c_base.receive_response(self.address, verbose=self.verbose)

        # Parsing Logic: Check for Response CMD 0x15 and LENGTH 1
        if response_cmd == 0x15 and len(payload) == 1:
            self.power = payload[0]
            if self.verbose:
                print(f"[Radiator] Fan PWM received: {self.power}%")
            return self.power
        else:
            return None
 
    def get_temperatures(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Requests and parses the two temperature values (Response CMD 0x12, 4 bytes).
        Uses GET command (0x02 for Temperature).
        """
        i2c_base.send_command(self.address, 0, 0x02, verbose=self.verbose)
        time.sleep(0.5) 
        response_cmd, payload = i2c_base.receive_response(self.address, verbose=self.verbose)
 
        # Parsing Logic: Check for Response CMD 0x12 and LENGTH 4
        if response_cmd == 0x12 and len(payload) == 4:
            self.temp_in = (payload[0] | (payload[1] << 8)) / 100.0
            self.temp_out = (payload[2] | (payload[3] << 8)) / 100.0
            if self.verbose:
                print(f"[Radiator] Temp received: In={self.temp_in:.2f}°C, Out={self.temp_out:.2f}°C")
            return self.temp_in, self.temp_out
        else:
            if self.verbose: 
                print(f"[Radiator] Error: Incomplete data (Expected 4 bytes, received {len(payload)}).")
            return None, None
 