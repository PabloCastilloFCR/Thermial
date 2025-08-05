import sys
import os
import time

# Agrega la ruta de la carpeta custom_code al sys.path
# La línea siguiente navega un nivel hacia arriba (..),
# luego busca la carpeta 'custom_code'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'custom_code'))

# Ahora puedes importar el módulo thermial
from thermial import Loop

loop = Loop(verbose = True)
#loop.set_abrir_valvula(1)
#time.sleep(2)
#loop.set_abrir_valvula(2)
#loop.set_potencia_bomba(1, 100)
#time.sleep(3)
loop.stop()
#time.sleep(5)
