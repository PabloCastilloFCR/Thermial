import sys
import os
import time

# Add drivers directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
drivers_dir = os.path.join(os.path.dirname(current_dir), '2_controller', '2.1_drivers')
if drivers_dir not in sys.path:
    sys.path.append(drivers_dir)

from pumps_i2c import Pump
from heater_i2c import Heater1
from heater_two_i2c import Heater2
from valves_i2c import Valves
from tank_i2c import Tank
from radiator_i2c import Radiator1

def test_pumps():
    print("\n--- Testing Pumps ---")
    p1 = Pump(device_key="PUMP1_SOLAR_LOOP", verbose=True)
    p2 = Pump(device_key="PUMP2_PROCESS_LOOP", verbose=True)
    
    for p in [p1, p2]:
        print(f"Testing {p.device_name}...")
        p.set_power(50)
        time.sleep(1)
        flow = p.get_flow()
        print(f"Result -> Power: {p.power}%, Flow: {flow:.2f} L/min")
        p.set_power(0)
        print(f"{p.device_name} stopped.")

def test_heaters():
    print("\n--- Testing Heaters ---")
    h1 = Heater1(device_key="HEATER1_SOLAR_LOOP", verbose=True)
    h2 = Heater2(device_key="HEATER2_SOLAR_LOOP", verbose=True)
    
    print("Testing Heater 1...")
    h1.set_pwm_heater1(20)
    time.sleep(1)
    t_in, t_out = h1.get_temperatures()
    print(f"Result -> PWM: {h1.power}%, In: {t_in:.2f}°C, Out: {t_out:.2f}°C")
    h1.set_pwm_heater1(0)
    
    print("Testing Heater 2...")
    h2.set_pwm_heater2(20)
    time.sleep(1)
    t_out = h2.get_temperatures()
    print(f"Result -> PWM: {h2.power}%, Out: {t_out:.2f}°C")
    h2.set_pwm_heater2(0)

def test_valves():
    print("\n--- Testing Valves ---")
    v = Valves(device_key="VALVES", verbose=True)
    
    print("Opening Valve 1...")
    v.open_valve(1)
    time.sleep(1)
    print("Opening Valve 2...")
    v.open_valve(2)
    time.sleep(1)
    
    f1, f2 = v.get_flows()
    print(f"Result -> Flow1: {f1:.2f}, Flow2: {f2:.2f}, State1: {v.state_valve1}, State2: {v.state_valve2}")
    
    print("Closing Valve 1...")
    v.close_valve(1)
    print("Closing Valve 2...")
    v.close_valve(2)

def test_tank():
    print("\n--- Testing Tank Sensors ---")
    t = Tank(device_key="HEAT_STORAGE", verbose=True)
    
    level = t.get_level()
    t_bottom, t_top = t.get_temperatures()
    print(f"Result -> Level: {level:.2f} cm, Bottom: {t_bottom:.2f}°C, Top: {t_top:.2f}°C")

def test_radiator():
    print("\n--- Testing Radiator ---")
    r = Radiator1(device_key="RADIATOR_PROCESS_LOOP", verbose=True)
    
    print("Setting Radiator Fan to 50%...")
    r.set_power_radiator1(50)
    time.sleep(1)
    t_in, t_out = r.get_temperatures()
    print(f"Result -> PWM: {r.power}%, In: {t_in:.2f}°C, Out: {t_out:.2f}°C")
    r.set_power_radiator1(0)
    print("Radiator Fan stopped.")

if __name__ == "__main__":
    print("Starting Thermial System Verification Test")
    try:
        test_pumps()
        test_heaters()
        test_valves()
        test_tank()
        test_radiator()
        print("\nVerification Test Completed Successfully")
    except Exception as e:
        print(f"\nTest Failed with error: {e}")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
