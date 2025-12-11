import time
import os
import sys
 
# --- Path Definition --- 
current_dir = os.path.dirname(os.path.abspath(__file__)) # current path: 3.2_logic
logic_dir = os.path.dirname(current_dir) #goes to 2_controller
drivers_path = os.path.join(logic_dir, '2.1_drivers')
sys.path.append(drivers_path)
# -----------------------
 
from valves_i2c import Valve
 
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
            valve_module.get_flows_and_status()
            time.sleep(3) 

    except KeyboardInterrupt:
        print("Stopping Valve Test")
        # Ensure both valves are closed on exit
        valve_module.close_valve(1)
        valve_module.close_valve(2)
        print("All Valves CLOSED.")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")