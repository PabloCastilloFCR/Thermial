#from modulo_bomba_flujometro import Bomba
#from modulo_valvulas_loop_termico import Valvulas
from bomba_i2c import Pump    
from dos_valvulas_i2c import Valves    
from calentador_i2c import Heater1
from calentador_dos_i2c import Heater2
from disipador_i2c import Radiator1

pump1 = Pump(address=0x10)
pump2 = Pump(address=0x14)

#bomba = Bomba()
valves = Valves()
heater1 = Heater1()
heater2 = Heater2()
radiator1 = Radiator1()
pump1.set_power(0)
pump2.set_power(0)
#valves.open_valve(1)
#valves.open_valve(2)
valves.close_valve(1)
valves.close_valve(2)
heater1.set_pwm_heater1(0)
heater2.set_pwm_heater2(0)
radiator1.set_pwm_fan(0)

