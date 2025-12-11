import i2c_0x16  # Modul mit send_command() und receive_response()
import time
from i2c_address import load_i2c_address

class Heater2:
    def __init__(self, device_key="HEATER2_SOLAR_LOOP", verbose=False):
        self.address = load_i2c_address(device_key)
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        #self.address = 0x16
        self.device_name = "Heater 2"
        self.power = 0
        self.temp_out = 0.0
        

    def set_pwm_heater2(self, pwm_value):
        """
        Setea valor PWM del calentador (0–100%).
        """
        if not 0 <= pwm_value <=100:
            raise ValueError("PWM debe estar entre 0 y 100")
        i2c_0x16.send_command(self.address, 0, 0x01, [int(pwm_value)])
        time.sleep(0.1)
        self.power = pwm_value

    def get_temperatures(self):
        """
        Requests and returns the two values from the temperature sensors.
        :return: (temp_radiator1_in, temp_radiator1_out) or nothing if there is an error
        """
        i2c_0x16.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        self.temp_out = i2c_0x16.receive_response(self.address)