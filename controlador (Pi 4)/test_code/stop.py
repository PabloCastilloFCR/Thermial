#from modulo_bomba_flujometro import Bomba
#from modulo_valvulas_loop_termico import Valvulas
from bomba_i2c import Bomba    
from valvulas_i2c import Valvulas    
from calentador_i2c import Calentador

bomba1 = Bomba(address=0x10)
bomba2 = Bomba(address=0x14)

#bomba = Bomba()
valvulas = Valvulas()
calentador = Calentador()
bomba1.set_potencia(0)
bomba2.set_potencia(0)
#bomba.set_potencia(0)
#valvulas.abrir_valvula(1)
#valvulas.abrir_valvula(2)
valvulas.cerrar_valvula(1)
valvulas.cerrar_valvula(2)
calentador.set_pwm_calentador(0)