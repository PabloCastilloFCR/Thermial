import i2c_0x10
import time


class Pump:
    def __init__(self, address=0x10):
        self.address = address
        self.device_name = "Modulo Bomba Flujometro"
        self.power = 0
        self.flow = 0

    def set_power(self, power: int):
        """
        Setea la potencia de la bomba.
        :param potencia: Potencia de la bomba (0-100).
        """

        if not 0 <= power <= 100:
            raise ValueError("La potencia debe estar entre 0 y 100")

        i2c_0x10.send_command(self.address, 0, 0x01, [int(power)])
        self.power = power

    def get_flow(self):
        """
        Solicita y devuelve el flujo actual de la bomba.
        :return: Flujo actual de la bomba.
        """
        i2c_0x10.send_command(self.address, 0, 0x02)
        time.sleep(0.1)
        self.flow = i2c_0x10.receive_response(self.address, False)
        return self.flow

        

