from modulo_bomba_flujometro import Bomba    
from modulo_valvulas import Valvulas
import time  

bomba = Bomba()
valvulas = Valvulas()
time.sleep(5)
print("Ejectando test 1")

#time.sleep(10)
bomba.set_potencia(00)


while True:
    print("Abriendo valvula 2")
    valvulas.abrir_valvula(1)
    print("Esperando 10 seg")
    time.sleep(10)
    valvulas.cerrar_valvula(1)
    print("Abriendo valvula 2")
    valvulas.abrir_valvula(2)
    print("Esperando 10 seg")
    time.sleep(10)
    print("Cerrando valvula 2")
    valvulas.cerrar_valvula(2)