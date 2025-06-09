import i2c_0x12  
import time

class Valvulas:
    def __init__(self):
        self.address = 0x12
        self.device_name = "Modulo Valvulas"

    def abrir_valvula(self, numero):
        """
        Abre una válvula específica.
        :param numero: 1 para válvula 1, 2 para válvula 2
        """
        if numero == 1:
            i2c_0x12.send_command(self.address, 0x01, [1])
        elif numero == 2:
            i2c_0x12.send_command(self.address, 0x01, [2])
        else:
            raise ValueError("Solo puedes sólo puede pasar un valor entre 1 y 2")

    def cerrar_valvula(self, numero):
        """
        Cierra una válvula específica.
        :param numero: 1 para válvula 1, 2 para válvula 2
        """
        if numero == 1:
            i2c_0x12.send_command(self.address, 0x01, [3])
        elif numero == 2:
            i2c_0x12.send_command(self.address, 0x01, [4])
        else:
            raise ValueError("Solo puedes sólo puede pasar un valor entre 1 y 2")

    def get_flujos(self):
        """
        Solicita y devuelve los valores de los dos flujómetros.
        :return: (flow1, flow2)
        """
        i2c_0x12.send_command(self.address, 0x02, [])
        time.sleep(0.5)
        response = i2c_0x12.receive_response(self.address)
        if response is None:
            return None
        response_id, response_cmd, response_data = response

        if len(response_data) >= 4:
            flow1 = response_data[0] + (response_data[1] << 8)
            flow2 = response_data[2] + (response_data[3] << 8)
            flow1 /= 100.0
            flow2 /= 100.0
            return flow1, flow2
        else:
            return None
