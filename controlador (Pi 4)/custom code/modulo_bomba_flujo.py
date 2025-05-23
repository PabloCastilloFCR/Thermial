import I2C_0x10
import time


class Bomba:
    def __init__(self):
        self.address = 0x10
        self.device_name = "Modulo Bomba Flujometro"

    def set_potencia(self, potencia):
        """
        Setea la potencia de la bomba.
        :param potencia: Potencia de la bomba (0-100).
        """

        if not 0 <= potencia <= 100:
            raise ValueError("La potencia debe estar entre 0 y 100")
        I2C_0x10.send_command(self.address, 0, 0x01, [potencia])

    def get_flujo(self):
        """
        Solicita y devuelve el flujo actual de la bomba.
        :return: Flujo actual de la bomba.
        """
        I2C_0x10.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        response = I2C_0x10.receive_response(self.address)
        if response is None:
            return None
        response_id, response_cmd, response_data = response
        # Flusswert aus response_data extrahieren:
        # Bei deinem Code: response_data[0] + (response_data[1] << 8), dann unter 100 teilen
        if len(response_data) >= 2:
            flow_value = response_data[0] + (response_data[1] << 8)
            flow_value /= 100.0
            return flow_value
        else:
            return None
