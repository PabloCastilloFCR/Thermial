import i2c_0x10
import time


class Bomba:
    def __init__(self):
        self.address = 0x10
        self.device_name = "Modulo Bomba Flujometro"
        self.potencia = 0
        self.flujo = 0

    def set_potencia(self, potencia: int):
        """
        Setea la potencia de la bomba.
        :param potencia: Potencia de la bomba (0-100).
        """

        if not 0 <= potencia <= 100:
            raise ValueError("La potencia debe estar entre 0 y 100")

        i2c_0x10.send_command(self.address, 0, 0x01, [int(potencia)])
        self.potencia = potencia

    def get_flujo(self):
        """
        Solicita y devuelve el flujo actual de la bomba.
        :return: Flujo actual de la bomba.
        """
        i2c_0x10.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        self.flujo = i2c_0x10.receive_response(self.address)

        

