import i2c_0x12  
import time

class Valvulas:
    def __init__(self):
        self.address = 0x12
        self.device_name = "Modulo Valvulas"
        self.flow1 = 0
        self.flow2 = 0
        self.state_valve1 = None
        self.state_valve2 = None


    def abrir_valvula(self, numero):
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

    def cerrar_valvula(self, numero):
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

    def get_flujos(self):
        """
        Solicita y devuelve los valores de los dos flujómetros.
        """
        i2c_0x12.send_command(self.address, 0x02, [])
        time.sleep(0.5)
        self.flow1, self.flow2, _, _ = i2c_0x12.receive_response(self.address)
        
