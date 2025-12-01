import i2c_0x15  # Modul mit send_command() und receive_response()
import time


class Disipador:
    def __init__(self):
        self.address = 0x15
        self.device_name = "Modulo Disipador"
        self.potencia = 0
        self.temp5 = 0
        self.temp6 = 0


    def set_pwm_ventilador(self, pwm_value):
        """
        Setea valor PWM del ventilador (0–100%).
        """
        if not 0 <= pwm_value <=100:
            raise ValueError("PWM debe estar entre 0 y 100")
        i2c_0x15.send_command(self.address, 0, 0x01, [int(pwm_value)])
        self.potencia = pwm_value

    def get_temperaturas(self):
        """
        Solicita y devuelve los dos valores de los sensores de temperatura.
        :return: (t1, t2) ó ninguno cuando ocurre un error
        """
        i2c_0x15.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        self.temp5, self.temp6 = i2c_0x15.receive_response(self.address)
        #print(f"temperatura recibida: Temp5 = {self.temp5:.2f}°C, Temp6 = {self.temp6:.2f}°C")
        