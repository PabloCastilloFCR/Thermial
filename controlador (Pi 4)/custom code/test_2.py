from wrapper_loop_termico import SolarLoop
import time

loop = SolarLoop(verbose= True)

print("Prueba 1: Abrir Valvula 1. Encender Bomba 10 segundos. Apagar todo.")
time.sleep(3)
loop.abrir_valvula(1)
time.sleep(1)
loop.potencia_bomba(80)
time.sleep(1)
loop.print_status()
time.sleep(10)
loop.stop()
time.sleep(1)
loop.print_status()

