from calentador_dos_i2c import Calentadordos
import time

print("Teste Calentadordos...")
cal2 = Calentadordos()

print("Rufe get_temperaturas() auf...")
try:
    cal2.get_temperatures()
    print(f"Erfolg! Temp7: {cal2.temp7}")
except Exception as e:
    print(f"FEHLER: {e}")
    import traceback
    traceback.print_exc()