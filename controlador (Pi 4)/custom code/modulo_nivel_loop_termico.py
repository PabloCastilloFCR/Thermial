import i2c_0x13
import time

class Nivel:
    def __init__(self):
        self.address = 0x13
        self.device_name = "Modulo Nivel"

    def get_temperaturas(self):
        i2c_0x13.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        response = i2c_0x13.receive_response(self.address)
        if response is None:
            return None
        response_id, response_cmd, response_data = response

        if len(response_data) >= 4:
            temp3 = (response_data[0] | (response_data[1] << 8)) / 100.0
            temp4 = (response_data[2] | (response_data[3] << 8)) / 100.0
            return temp3, temp4
        else:
            return None

    def get_nivel(self):
        i2c_0x13.send_command(self.address, 0, 0x03)
        time.sleep(0.5)
        response = i2c_0x13.receive_response(self.address)
        if response is None:
            return None
        response_id, response_cmd, response_data = response

        if len(response_data) >= 2:
            nivel = response_data[0] | (response_data[1] << 8)
            return nivel
        else:
            return None
