import time
from i2c_address import load_i2c_address 
from i2c_base import send_command, receive_response

 
class Heater:
    def __init__(self, device_key: str, verbose=False):
        # Load address based on the key (HEATER1_SOLAR_LOOP or HEATER2_SOLAR_LOOP)
        self.address = load_i2c_address(device_key)
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        self.device_key = device_key # Store key to distinguish between H1 (4 bytes) and H2 (2 bytes)
        self.device_name = f"Heater Module ({device_key})"
        self.power = 0
        self.temp_in = 0.0
        self.temp_out = 0.0
        self.verbose = verbose
 
    # --- Common SET/GET PWM Logic ---
 
    def set_pwm(self, pwm_value: int):
        """Sets the PWM value for the heater (0-100%). Uses SET command (0x01)."""
        if not 0 <= pwm_value <= 100:
            raise ValueError("PWM must be between 0 and 100")
        send_command(self.address, 0, 0x01, [int(pwm_value)], verbose=self.verbose)
        time.sleep(0.1)
        self.power = pwm_value
    def get_pwm(self):
        """Requests and parses the current PWM value (Response CMD 0x15)."""
        send_command(self.address, 0, 0x01, verbose=self.verbose)
        time.sleep(0.5) 
        response_cmd, payload = receive_response(self.address, verbose=self.verbose)
        if response_cmd == 0x15 and len(payload) == 1:
            self.power = payload[0]
            if self.verbose:
                print(f"[Heater] PWM received: {self.power}%")
            return self.power
        else:
            return None
 
    # --- Differentiated GET Temperature Logic ---
 
    def _parse_temp_response(self, response_cmd, payload):
        """Internal method to parse the temperature response based on the device key."""
        if response_cmd != 0x12:
            if self.verbose: print(f"[Heater] Unexpected temp response CMD ({response_cmd:02x}).")
            return None, None
        # Heater 1 (0x11) expects 4 bytes (Temp In and Temp Out)
        if self.device_key == "HEATER1_SOLAR_LOOP":
            if len(payload) == 4:
                self.temp_in = (payload[0] | (payload[1] << 8)) / 100.0
                self.temp_out = (payload[2] | (payload[3] << 8)) / 100.0
                if self.verbose:
                    print(f"[Heater 1] Temp: In={self.temp_in:.2f}°C, Out={self.temp_out:.2f}°C")
                return self.temp_in, self.temp_out
            else:
                if self.verbose: print(f"[Heater 1] Error: Expected 4 bytes, received {len(payload)}.")
                return None, None
        # Heater 2 (0x16) expects 2 bytes (Only Temp Out)
        elif self.device_key == "HEATER2_SOLAR_LOOP":
            if len(payload) == 2:
                self.temp_out = (payload[0] | (payload[1] << 8)) / 100.0
                self.temp_in = 0.0 # Set unused sensor to 0.0 for consistency
                if self.verbose:
                    print(f"[Heater 2] Temp: Out={self.temp_out:.2f}°C")
                return self.temp_out, None # Return Temp_Out and None for Temp_In
            else:
                if self.verbose: print(f"[Heater 2] Error: Expected 2 bytes, received {len(payload)}.")
                return None, None
 
    def get_temperatures(self):
        """Requests temperature and uses the internal parser."""
        send_command(self.address, 0, 0x02, verbose=self.verbose)
        time.sleep(0.5) 
        response_cmd, payload = receive_response(self.address, verbose=self.verbose)
        # Call the correct parser
        return self._parse_temp_response(response_cmd, payload)