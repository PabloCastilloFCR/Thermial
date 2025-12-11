import os
import sys
 
# --- Path Definition --- 
# This logic ensures the drivers in 2.1_drivers are found
current_dir = os.path.dirname(os.path.abspath(__file__))
controller_dir = os.path.dirname(current_dir) # one level up to 2_controller
drivers_path = os.path.join(controller_dir, '2.1_drivers')
sys.path.append(drivers_path)
# --- Corrected Imports from 2.1_drivers ---
# Use the unified module names
from pumps_i2c import Pump 
from valves_i2c import Valve 
from heaters_i2c import Heater
from radiator_i2c import Radiator
# ------------------------------------------
 
# --- Instantiation with JSON Keys and Unified Classes ---
 
# Pumps (use Pump class with specific keys)
pump1 = Pump(device_key="PUMP1_SOLAR_LOOP")
pump2 = Pump(device_key="PUMP2_PROCESS_LOOP")
 
# Valves (use Valve class)
valves = Valve(device_key="VALVES")
 
# Heaters (use Heater class with specific keys)
heater1 = Heater(device_key="HEATER1_SOLAR_LOOP")
heater2 = Heater(device_key="HEATER2_SOLAR_LOOP")
 
# Radiator (use Radiator class)
radiator1 = Radiator(device_key="RADIATOR_PROCESS_LOOP")
 
 
# --- Shutdown Execution (Unified Methods) ---
 
print("[STOPIT] Initializing emergency shutdown sequence...")
 
# Pumps (use unified set_power)
pump1.set_power(0)
pump2.set_power(0)
print("[STOPIT] Pumps 1 & 2 set to 0% power.")
 
# Valves (use unified close_valve method)
valves.close_valve(1)
valves.close_valve(2)
print("[STOPIT] Valves 1 & 2 commanded to CLOSE.")
 
# Heaters (use unified set_pwm method)
heater1.set_pwm(0)
heater2.set_pwm(0)
print("[STOPIT] Heaters 1 & 2 set to 0% PWM.")
 
# Radiator (use unified set_pwm method)
radiator1.set_pwm(0)
print("[STOPIT] Radiator Fan set to 0% PWM.")
 
print("[STOPIT] Shutdown complete. All actuators OFF/CLOSED.")