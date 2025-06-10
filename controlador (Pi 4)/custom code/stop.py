from modulo_bomba_loop_termico_nuevo import Bomba
from modulo_valvulas_loop_termico import Valvulas

bomba = Bomba()
valvulas = Valvulas()
bomba.set_potencia(0)
valvulas.abrir_valvula(1)
valvulas.abrir_valvula(2)