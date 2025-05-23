import I2C_0x11  # Modul mit send_command() und receive_response()
import time


class Calentador:
    def __init__(self):
        self.address = 0x11
        self.device_name = "Modulo Calentador"

    def set_pwm(self, pwm_value):
        """
        Setea valor PWM del calentador (0–100%).
        """
        if not 0 <= pwm_value <= 100:
            raise ValueError("PWM debe estar entre 0 y 100")
        I2C_0x11.send_command(self.address, 0, 0x01, [pwm_value])

    def get_temperaturas(self):
        """
        Solicita y devuelve los dos valores de los sensores de temperatura.
        :return: (temp1, temp2) ó ninguno cuando ocurre un error
        """
        I2C_0x11.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        response = I2C_0x11.receive_response(self.address)
        if response is None:
            return None
        response_id, response_cmd, response_data = response
        if response_cmd == 0x12 and len(response_data) == 4:
            data = response_data
            temp1 = (data[0] + (data[1] << 8)) / 100.0
            temp2 = (data[2] + (data[3] << 8)) / 100.0
            return temp1, temp2
        else:
            return None
