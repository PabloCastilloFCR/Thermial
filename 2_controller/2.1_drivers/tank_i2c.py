import i2c_0x13
import time
from i2c_address import load_i2c_address

class Tank:
    def __init__(self, device_key="HEAT_STORAGE", verbose=False):
        self.address = load_i2c_address(device_key)
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        #self.address = 0x13
        self.device_name = "Tank"
        self.level = None
        self.temp_bottom = 0.0
        self.temp_top = 0.0


    def get_temperatures(self):
        """
        Requests and returns the two values from the temperature sensors.
        :return: (temp_radiator1_in, temp_radiator1_out) or nothing if there is an error
        """
        i2c_0x13.send_command(self.address, 0, 0x02)
        time.sleep(0.5)
        raw_result = i2c_0x13.receive_response(self.address)
        print(f"[DEBUG TANK] Raw response for temps: {raw_result}")
        if isinstance(raw_result, (list, tuple)) and len(raw_result) == 2:
            self.temp_bottom, self.temp_top = raw_result
        else:
            self.temp_bottom = -1
            self.temp_top = -1
            
        #self.temp_bottom, self.temp_top = i2c_0x13.receive_response(self.address)
        #print(f"temperatures received: temp_in = {self.temp_in:.2f}°C, temp_out = {self.temp_out:.2f}°C")

    def get_level(self):
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
            level = max(0.0, tank_height - measured_distance)
            self.level = level
            print(f"Level received: {measured_distance:.2f} cm")
        
        elif len(response_data) == 1:
            self.level = response_data[0]
            #print(f"Distancia recibida: {self.nivel:.2f} cm")

        else:
            self.level = -1
