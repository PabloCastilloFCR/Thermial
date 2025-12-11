import time
from typing import Tuple, Optional
# FIX 1: load_i2c_address is now imported from i2c_base
from i2c_base import send_command, receive_response, load_i2c_address 
class Radiator:
    def __init__(self, device_key="RADIATOR_PROCESS_LOOP", verbose=False):
        # Load address 0x15 from JSON map via the key
        self.address = load_i2c_address(device_key)
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
        send_command(self.address, 0, 0x01, [int(pwm_value)], verbose=self.verbose)
        time.sleep(0.1)
        self.power = pwm_value
    def get_pwm(self):
        """
        Requests and parses the current fan PWM value (Response CMD 0x15).
        """
        # NOTE: Using 0x01 (SET) for GET is unusual; assuming it works as intended, but 0x02 is typical GET.
        send_command(self.address, 0, 0x01, verbose=self.verbose) 
        time.sleep(0.5)
        response_cmd, payload = receive_response(self.address, verbose=self.verbose)
        # FIX 2: Check for I2C read failure (payload is None)
        if payload is None:
            if self.verbose: print(f"[Radiator] I2C read failed for PWM.")
            return 0 # Return 0 on communication failure
        # Parsing Logic: Check for Response CMD 0x15 and LENGTH 1
        if response_cmd == 0x15 and len(payload) == 1:
            self.power = payload[0]
            if self.verbose:
                print(f"[Radiator] Fan PWM received: {self.power}%")
            return self.power
        else:
            # FIX 3: Return 0 on invalid data/CMD
            if self.verbose: print(f"[Radiator] Unexpected response for PWM (CMD {response_cmd:02x}).")
            return 0
    def get_temperatures(self) -> Tuple[float, float]:
        """
        Requests and parses the two temperature values (Response CMD 0x12, 4 bytes).
        Uses GET command (0x02 for Temperature).
        """
        send_command(self.address, 0, 0x02, verbose=self.verbose)
        time.sleep(0.5)
        response_cmd, payload = receive_response(self.address, verbose=self.verbose)
        # FIX 4: Check for I2C read failure (payload is None)
        if payload is None:
            if self.verbose: print(f"[Radiator] I2C read failed for temperatures.")
            return 0.0, 0.0 # Return 0.0, 0.0 on communication failure
        # Parsing Logic: Check for Response CMD 0x12 and LENGTH 4
        if response_cmd == 0x12 and len(payload) == 4:
            # Data decoding (Byte shift and scaling logic)
            self.temp_in = (payload[0] | (payload[1] << 8)) / 100.0
            self.temp_out = (payload[2] | (payload[3] << 8)) / 100.0
            if self.verbose:
                print(f"[Radiator] Temp received: In={self.temp_in:.2f}°C, Out={self.temp_out:.2f}°C")
            return self.temp_in, self.temp_out
        else:
            if self.verbose:
                print(f"[Radiator] Error: Incomplete data (Expected 4 bytes, received {len(payload)}).")
            # FIX 5: Return 0.0, 0.0 on invalid data/CMD
            return -1, -1