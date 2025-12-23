import time
import os
import sys

# --- Path Definition --- 
current_dir = os.path.dirname(os.path.abspath(__file__)) 
thermial_root = os.path.dirname(os.path.dirname(current_dir)) # goes to root (Thermial)
drivers_path = os.path.join(thermial_root, '2_controller', '2.1_drivers')
sys.path.append(drivers_path)
# -----------------------

from pumps_i2c import Pump


if __name__ == "__main__":
    pump_module = Pump(device_key="PUMP1_SOLAR_LOOP", verbose=True)

    # Werte für Stresstest
    values_to_test = [70, 75, 80, 85, 90, 95, 100]
    cycles = 100  # wie oft die Sequenz wiederholt wird

    for cycle in range(cycles):
        print(f"\n--- Cycle {cycle+1}/{cycles} ---")
        for value in values_to_test:
            try:
                # SET-Befehl
                pump_module.set_power(value)
                time.sleep(0.05) 

                # GET-Befehl/Response
                resp = pump_module.get_flow()
                if resp is None:
                    print(f"Warnung: Keine Antwort bei Wert {value}")

            except Exception as e:
                print(f"Fehler bei Wert {value}: {e}")

    # Am Ende alles auf 0 setzen
    pump_module.set_power(0)
    time.sleep(0.5)
    print("Stresstest beendet, alle Werte auf 0 gesetzt.")
