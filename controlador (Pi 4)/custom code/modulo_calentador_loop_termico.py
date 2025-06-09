import i2c_0x11  # Modul mit send_command() und receive_response()
import time


class Calentador:
    def __init__(self):
        self.address = 0x11
        self.device_name = "Modulo Calentador"
        self.potencia = 0
        self.temp1 = 0
        self.temp2 = 0


    def set_pwm_calentador(self, pwm_value):
        """
        Setea valor PWM del calentador (0–100%).
        """
        if not 0 <= pwm_value <=100:
            raise ValueError("PWM debe estar entre 0 y 100")
        i2c_0x11.send_command(self.address, 0, 0x01, [int(pwm_value)])
        self.potencia = pwm_value

    def get_temperaturas(self):
        """
        Solicita y devuelve los dos valores de los sensores de temperatura.
        :return: (t1, t2) ó ninguno cuando ocurre un error
        """
        i2c_0x11.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        self.temp1, self.temp2 = i2c_0x11.receive_response(self.address)
        