import FCR_I2C
import time


class Bomba:
    def __init__(self):
        self.address = 0x10
        self.device_name = "Modulo Bomba Flujometro"

    def setear_potencia_bomba(self, potencia):
        """
        Setea la potencia de la bomba.
        :param potencia: Potencia de la bomba (0-100).
        """
        if not 0 <= potencia <= 100:
            raise ValueError("La potencia debe estar entre 0 y 100")
        else:
            I2C_0x10.send_command(self.address, 0, 0x01, [potencia])

    def obtener_flujo(self):
        """
        Obtiene el flujo actual de la bomba.
        :return: Flujo actual de la bomba.
        """
        I2C_0x10.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        id, cmd, data = I2C_0x10.receive_response(self.address)
        return data

