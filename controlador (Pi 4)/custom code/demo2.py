from wrapper_sistema_completo_dos_bombas import SolarLoop, ProcessLoop, export_to_csv, clear_data_log
import time
import threading
from datetime import datetime
import shutil

solar_loop = SolarLoop(verbose=True)
process_loop = ProcessLoop(verbose=True)

print("[Setup] Cerrando válvulas 1 y 2 para comenzar desde cero...")
solar_loop.cerrar_valvula(1)
solar_loop.cerrar_valvula(2)
time.sleep(1)

# Sicheres Logging – wartet mit process_loop, bis bomba2 initialisiert ist
def log_all_data():
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    solar_loop.append_to_data_log(timestamp)

    try:
        _ = process_loop.bomba.flujo  # Test, ob initialisiert
        process_loop.append_to_data_log(timestamp)
    except (AttributeError, TypeError):
        print("[Log] ProcessLoop noch nicht bereit – Daten werden übersprungen.")

print("Iniciando test del SolarLoop y ProcessLoop...")

solar_loop.stop()
process_loop.stop()
clear_data_log()

# Schneller Start
solar_loop.potencia_calentador(100)
solar_loop.abrir_valvula(1)
log_all_data()

# Funktion für 1 Demo-Zyklus
def demo_cycle(cycle_number):
    print(f"[Demo] Ciclo {cycle_number + 1}/3")

    # Direkt loslegen
    solar_loop.potencia_bomba1(85)
    print(f"[{cycle_number + 1}] Bomba1 al 85%")
    log_all_data()

    def bomba1_step2():
        time.sleep(30)
        solar_loop.potencia_bomba1(100)
        print(f"[{cycle_number + 1}] Bomba1 al 100%")
        log_all_data()

    def dissipador_step():
        time.sleep(20)
        process_loop.potencia_dissipador(100)
        print(f"[{cycle_number + 1}] Dissipador al 100%")
        log_all_data()

    def bomba2_step():
        time.sleep(30)
        process_loop.potencia_bomba2(80)
        print(f"[{cycle_number + 1}] Bomba2 al 80%")
        log_all_data()

    def ventilator_pause_logic():
        # Warte auf das Zyklusende
        time.sleep(60)
        print(f"[{cycle_number + 1}] Pumpen gestoppt, Ventilator bleibt aktiv.")

        # Beobachte, ob eine Pumpe wieder aktiv wird
        while True:
            try:
                estado_b1 = solar_loop.estado_bomba1
                estado_b2 = process_loop.estado_bomba2
            except AttributeError:
                estado_b1 = 0
                estado_b2 = 0

            if estado_b1 > 0 or estado_b2 > 0:
                print(f"[{cycle_number + 1}] Eine Pumpe wieder aktiv – Ventilator schaltet kurz ab.")
                process_loop.potencia_dissipador(0)
                log_all_data()
                time.sleep(15)
                process_loop.potencia_dissipador(100)
                print(f"[{cycle_number + 1}] Ventilator wieder an.")
                log_all_data()
                break
            time.sleep(1)

    # Threads starten
    threading.Thread(target=bomba1_step2).start()
    threading.Thread(target=dissipador_step).start()
    threading.Thread(target=bomba2_step).start()
    threading.Thread(target=ventilator_pause_logic).start()

    # Hauptthread schaltet Pumpen ab – Ventilator bleibt aktiv
    time.sleep(60)
    solar_loop.potencia_bomba1(0)
    process_loop.potencia_bomba2(0)
    # dissipador bleibt AN!
    log_all_data()

# Starte 3 Zyklen
for i in range(3):
    demo_cycle(i)

# Am Ende alles sicher abschalten
solar_loop.potencia_bomba1(0)
solar_loop.potencia_calentador(0)
process_loop.potencia_bomba2(0)
process_loop.potencia_dissipador(0)
log_all_data()

# Exportieren
csv_file = export_to_csv()
demo_file = "demo.csv"
shutil.move(csv_file, demo_file)

print(f"¡Terminado! Archivo Excel: {demo_file}")
