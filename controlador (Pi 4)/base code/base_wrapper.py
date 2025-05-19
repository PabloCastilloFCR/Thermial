import I2C_0x10


class Bomba:
    def __init__(self):
        self.address = 0x10
        self.device_name = "Modulo Bomba Flujometro"

    def setear_potencia_bomba(potencia):
        """
        Setea la potencia de la bomba.
        :param potencia: Potencia de la bomba (0-100).
        """
        if not 0 <= potencia <= 100:
            raise ValueError("La potencia debe estar entre 0 y 100")
        else:
            I2C_0x10.send_command(self.address, 0, 0x01, [potencia])


