import time
import os
import sys
 
# --- Path Definition --- 
current_dir = os.path.dirname(os.path.abspath(__file__)) 
thermial_root = os.path.dirname(os.path.dirname(current_dir)) # goes to root (Thermial)
drivers_path = os.path.join(thermial_root, '2_controller', '2.1_drivers')
sys.path.append(drivers_path)
# -----------------------
 
from valves_i2c import Valves as Valve
 
if __name__ == "__main__":
    valve_module = Valve(device_key="VALVES", verbose=True)
    print(f"--- Starting Valve Test at Address 0x{valve_module.address:02x} ---")
    try:
        # --- DEMONSTRATION OF VALVE CONTROL ---
        print("\n--- DEMONSTRATING ALL VALVE COMMANDS ---")
        # Open Valve 1
        print("COMMAND: Opening Valve 1 (V1)")
        valve_module.open_valve(1)
        time.sleep(1) 
        # Close Valve 1
        print("COMMAND: Closing Valve 1 (V1)")
        valve_module.close_valve(1)
        time.sleep(1)
        # Open Valve 2
        print("COMMAND: Opening Valve 2 (V2)")
        valve_module.open_valve(2)
        time.sleep(1)
        # Close Valve 2
        print("COMMAND: Closing Valve 2 (V2)")
        valve_module.close_valve(2)
        time.sleep(1)
        print("\n--- STARTING STATUS LOOP ---")
        # --- ORIGINAL STATUS LOOP ---
        while True:
            print("GET: Requesting Flows and Status")
            valve_module.get_flows()
            time.sleep(3) 

    except KeyboardInterrupt:
        print("Stopping Valve Test")
        # Ensure both valves are closed on exit
        valve_module.close_valve(1)
        valve_module.close_valve(2)
        print("All Valves CLOSED.")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")