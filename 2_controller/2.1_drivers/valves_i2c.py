import i2c_0x12  
import time
from i2c_address import load_i2c_address 

class Valves:
    def __init__(self, device_key="VALVES", verbose=False):
        self.address = load_i2c_address(device_key) 
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        #self.address = 0x12
        self.device_name = "Valves"
        self.flow_valve1_out = 0
        self.flow_valve2_out = 0
        self.state_valve1 = None
        self.state_valve2 = None


    def open_valve(self, numero):
        """
        Abre una válvula específica.
        :param numero: 1 para válvula 1, 2 para válvula 2
        """
        if numero == 1:
            i2c_0x12.send_command(self.address, 0x01, [3])
            self.state_valve1 = True
        elif numero == 2:
            i2c_0x12.send_command(self.address, 0x01, [4])
            self.state_valve2 = True
        else:
            raise ValueError("Solo puedes sólo puede pasar un valor entre 1 y 2")

    def close_valve(self, numero):
        """
        Cierra una válvula específica.
        :param numero: 1 para válvula 1, 2 para válvula 2
        """
        if numero == 1:
            i2c_0x12.send_command(self.address, 0x01, [1])
            self.state_valve1 = False
        elif numero == 2:
            i2c_0x12.send_command(self.address, 0x01, [2])
            self.state_valve2 = False
        else:
            raise ValueError("Solo puedes sólo puede pasar un valor entre 1 y 2")

    def get_flows(self):
        """
        Solicita y devuelve los valores de los dos flujómetros.
        """
        i2c_0x12.send_command(self.address, 0x02, [])
        time.sleep(0.5)
        self.flow_valve1_out, self.flow_valve2_out, _, _ = i2c_0x12.receive_response(self.address)
        
