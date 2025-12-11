import i2c_0x10 
import time
# Imports the necessary address resolution for the main Loop class
from i2c_address import load_i2c_address 

class Pump:
    def __init__(self, device_key="PUMP1_SOLAR_LOOP", verbose=False):
        # Dynamically fetch the address (0x10 or 0x14)
        self.address = load_i2c_address(device_key) 
        if self.address is None:
            raise ValueError(f"ERROR: Address for {device_key} could not be loaded.")
        self.device_name = "Pump 1"
        self.power = 0
        self.flow = 0.0 # Set to 0.0 for clean error handling in the main script
        # self.verbose is stored but not used in the I2C calls below
    def set_power(self, power: int):
        """
        Sets the pump power.
        :param power: Pump power (0-100).
        """
        if not 0 <= power <= 100:
            raise ValueError("La potencia debe estar entre 0 y 100")
        # Direct call to i2c_0x10 function, omitting the 'verbose' parameter 
        # (uses the default set in i2c_0x10.py).
        i2c_0x10.send_command(self.address, 0, 0x01, [int(power)])
        self.power = power
    def get_flow(self):
        """
        Requests and returns the current pump flow.
        :return: Current pump flow.
        """
        # Direct call, omitting 'verbose'
        i2c_0x10.send_command(self.address, 0, 0x02)
        # Using 0.5s sleep for stable I2C communication (avoids immediate timeout).
        time.sleep(0.5) 
        # Direct call, omitting 'verbose'
        # NOTE: If you need verbose output here, you must pass the flag: 
        # i2c_0x10.receive_response(self.address, self.verbose)
        self.flow = i2c_0x10.receive_response(self.address, False)
        # Error handling: If communication failed (i2c_0x10 returns None), set to 0.0
        if self.flow is None:
            self.flow = 0.0 
        return self.flow