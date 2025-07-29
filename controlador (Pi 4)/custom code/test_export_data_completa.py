from wrapper_sistema_completo import SolarLoop, ProcessLoop, export_to_csv, clear_data_log
import time
import threading
from datetime import datetime

solar_loop = SolarLoop(verbose=True)
process_loop = ProcessLoop(verbose=True)

def log_all_data():
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    solar_loop.append_to_data_log(timestamp)
    process_loop.append_to_data_log(timestamp)


print("Iniciando test del SolarLoop y ProcessLoop...")

solar_loop.stop()
process_loop.stop()
clear_data_log()

solar_loop.potencia_calentador(75)
log_all_data()


solar_loop.abrir_valvula(1)
log_all_data()


print("Esperando 10 segundos...")
time.sleep(10)

solar_loop.potencia_bomba(85)
log_all_data()


process_loop.potencia_dissipador(85)
log_all_data()


print("Haciendo mediciones")

# Funktionen, um beide Tests gleichzeitig zu starten
def solar_test():
    solar_loop.run_synchronized_test(process_loop, duration_minutes=1, interval_seconds=30)        # testeando solar loop para x minutos, colectando datos cada y segundos

def process_test():
    pass

# Threads mit klaren Namen
solar_thread = threading.Thread(target=solar_test)
process_thread = threading.Thread(target=process_test)

solar_thread.start()
process_thread.start()

solar_thread.join()
process_thread.join()

solar_loop.potencia_bomba(0)
solar_loop.potencia_calentador(0)
process_loop.potencia_dissipador(0)
log_all_data()


csv_file = export_to_csv()
print(f"¡Terminado! Archivo Excel: {csv_file}")
