import i2c_0x15  # Modul mit send_command() und receive_response()
import time
from i2c_address import load_i2c_address

class Radiator1:
    def __init__(self, device_key="RADIATOR_PROCESS_LOOP", verbose=False):
        self.address = load_i2c_address(device_key)
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        #self.address = 0x15
        self.device_name = "Modulo Disipador"
        self.power = 0
        self.temp_in = 0
        self.temp_out = 0


    def set_pwm_fan(self, pwm_value):
        """
        Set PWM value of the fan (0–100%).
        """
        if not 0 <= pwm_value <=100:
            raise ValueError("PWM has to be between 0 and 100")
        i2c_0x15.send_command(self.address, 0, 0x01, [int(pwm_value)])
        self.power = pwm_value

    def get_temperatures(self):
        """
        Requests and returns the two values from the temperature sensors.
        :return: (temp_radiator1_in, temp_radiator1_out) or nothing if there is an error
        """
        i2c_0x15.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        self.temp_in, self.temp_out = i2c_0x15.receive_response(self.address)
        #print(f"temperatures received: temp_in = {self.temp_in:.2f}°C, temp_out = {self.temp_out:.2f}°C")
        

    