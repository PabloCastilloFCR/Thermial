import i2c_0x13
import time

class Estanque:
    def __init__(self):
        self.address = 0x13
        self.device_name = "Modulo Estanque"
        self.nivel = None
        self.temp3 = 0
        self.temp4 = 0

    def get_temperaturas(self):
        """
        Solicita y devuelve los dos valores de los sensores de temperatura.
        :return: (t1, t2) ó ninguno cuando ocurre un error
        """
        i2c_0x13.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        response = i2c_0x13.receive_response(self.address)
        if response is None:
            return None
        response_data = response

        if len(response_data) >= 4:
            temp3 = (response_data[0] | (response_data[1] << 8)) / 100.0
            temp4 = (response_data[2] | (response_data[3] << 8)) / 100.0
            self.temp3 = temp3
            self.temp4 = temp4
            #print(f"Temperatura recibida: Temp3 = {temp3:.2f}°C, Temp4 = {temp4:.2f}°C")
        
        elif len(response_data) == 2:
            self.temp3 = response_data[0]
            self.temp4 = response_data[1]
        else:
            self.temp3 = -1
            self.temp4 = -1

    def get_nivel(self):
        """
        Solicita y devuelve el nivel actual del estanque.
        :return: Nivel actual del estanque.
        """
        i2c_0x13.send_command(self.address, 0, 0x03)
        time.sleep(0.5)
        response = i2c_0x13.receive_response(self.address)
        if response is None:
            return None
        response_data = response

        if len(response_data) >= 2:
            lvl_raw = response_data[0] | (response_data[1] << 8)
            measured_distance = lvl_raw / 10.0
            tank_height = 40.0
            nivel = max(0.0, tank_height - measured_distance)
            self.nivel = nivel
            print(f"Nivel recibido: {measured_distance:.2f} cm")
        
        elif len(response_data) == 1:
            self.nivel = response_data[0]
            #print(f"Distancia recibida: {self.nivel:.2f} cm")

        else:
            self.nivel = -1
