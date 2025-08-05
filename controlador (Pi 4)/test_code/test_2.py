from wrapper_loop_termico import SolarLoop
import time

loop = SolarLoop(verbose=True)

print("Prueba 1: Abrir Valvula 1. Activar Bomba. Cerrar valvula 1.")
time.sleep(1)
loop.stop()
loop.abrir_valvula(1)
time.sleep(1)
loop.potencia_bomba(90)
loop.potencia_calentador(0)
time.sleep(7)
loop.obtener_flujo_bomba()
loop.obtener_flujos_valvulas()
loop.obtener_temperaturas_calentador()
loop.obtener_temperaturas_estanque()
loop.potencia_bomba(0)
#time.sleep(5)
#loop.cerrar_valvula(1)
#loop.print_status()

