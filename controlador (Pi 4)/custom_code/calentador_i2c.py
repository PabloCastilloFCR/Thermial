import i2c_0x11  # Modul mit send_command() und receive_response()
import time


class Heater1:
    def __init__(self):
        self.address = 0x11
        self.device_name = "Modulo Calentador"
        self.power = 0
        self.temp_in = 0
        self.temp_out = 0


    def set_pwm_heater1(self, pwm_value):
        """
        Setea valor PWM del calentador (0–100%).
        """
        if not 0 <= pwm_value <=100:
            raise ValueError("PWM debe estar entre 0 y 100")
        i2c_0x11.send_command(self.address, 0, 0x01, [int(pwm_value)])
        time.sleep(0.1)
        self.power = pwm_value

    def get_temperatures(self):
        """
        Requests and returns the two values from the temperature sensors.
        :return: (temp_radiator1_in, temp_radiator1_out) or nothing if there is an error
        """
        i2c_0x11.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        self.temp_in, self.temp_out = i2c_0x11.receive_response(self.address)
        #print(f"temperatures received: temp_in = {self.temp_in:.2f}°C, temp_out = {self.temp_out:.2f}°C")