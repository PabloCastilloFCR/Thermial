#Module imports
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__)) # .../2.2_services
controller_dir = os.path.dirname(current_dir)          # .../2_controller
drivers_path = os.path.join(controller_dir, '2.1_drivers')
 
if drivers_path not in sys.path:
    sys.path.append(drivers_path)
# --- ENDE PATH FIX ---

import logging
import time
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional
 
# CORRECTION: Simplified driver imports, as the Path/Address logic has been
# consolidated and fixed in i2c_base.py.
from pumps_i2c import Pump
from heater_i2c import Heater1
from heater_two_i2c import Heater2
from valves_i2c import Valves
from tank_i2c import Tank
from radiator_i2c import Radiator1
# ---------------------------------------------------------------------
# One-time configuration (e.g. in your main script)
# ---------------------------------------------------------------------
logger = logging.getLogger("loop")          # Choose a namespace for your module
handler = logging.StreamHandler()           # Print to stdout
fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
handler.setFormatter(logging.Formatter(fmt))
logger.addHandler(handler)
# Toggle verbosity here:
logger.setLevel(logging.INFO)    # verbose: INFO, DEBUG
# logger.setLevel(logging.WARNING)  # quiet: WARNING, ERROR, CRITICAL
def safe_call(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        # Catch common I2C OS Errors (Input/output error)
        except OSError as e:
            if e.errno == 5:
                self.errors = {
                "error_type": "Input/output error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "function": func.__name__,
                "recommendation": "check connection between Pi4 and Pi Picos"
                }
                self.log.error(f"OSError in {func.__name__}: Input/output error")
            elif e.errno == 110:
                self.errors = {
                    "error_type": "Connection timed out",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "function": func.__name__,
                    "recommendation": "check I2C devices with sudo i2cdetect -y 1"
                }
                self.log.error(f"OSError in {func.__name__}: Connection timed out")
        # Catch errors from driver methods returning None (which should now be 0.0)
        except TypeError as e:
            if "NoneType" in str(e):
                self.errors = {
                    "error_type": "NoneType response: unsupported format string passed to NoneType.__format__",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "function": func.__name__,
                    "recommendation": "I2C device returned no data, check sensors"
                }
                self.log.error(f"TypeError in {func.__name__}: {e}")
        except ValueError as e:
            if "too many values to unpack" in str(e):
                self.errors = {
                    "error_type": "Invalid I2C response length",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "function": func.__name__,
                    "recommendation": "I2C device returned more than 2 values. Inspect raw data from receive_response()."
                }
                self.log.error(f"ValueError in {func.__name__}: {e}")
    return wrapper
class Loop:
    """
    Solar loop controller interfacing with pumps, heaters, valves, tank, and radiator.
    All messages go to the 'loop' logger. Verbose = INFO level.
    """
    def __init__(self,
                 pump = Pump,  
                 heater1 = Heater1,
                 heater2 = Heater2,
                 valves = Valves,
                 tank = Tank,
                 radiator1 = Radiator1,
                 verbose = False):
        # Instance objects with device_key for address loading
        self.pump1 = Pump(device_key="PUMP1_SOLAR_LOOP")
        self.pump2 = Pump(device_key="PUMP2_PROCESS_LOOP")
        self.heater1 = Heater1(device_key="HEATER1_SOLAR_LOOP")
        self.heater2 = Heater2(device_key="HEATER2_SOLAR_LOOP")
        self.valves = Valves(device_key="VALVES")
        self.tank = Tank(device_key="HEAT_STORAGE")
        self.radiator1 = Radiator1(device_key="RADIATOR_PROCESS_LOOP")
        self.data_log = []  # List to store collected data points
        self.errors = {}
        # Set logger verbosity based on the 'verbose' flag
        if verbose:
            logging.getLogger("loop").setLevel(logging.INFO)
        else:
            logging.getLogger("loop").setLevel(logging.WARNING)
        self.log = logging.getLogger("loop")
    #Pumps#
    @safe_call
    def set_power_pump(self, number:int, power:int):
        """
        Set power for pump 1 or 2 (0-100).
        """
        print(f"[DEBUG] set_power_pump called: number={number}, power={power}")
        if power > 100:
            power = 100
        elif power < 0:
            power = 0
        if number == 1:
            self.pump1.set_power(power)
            time.sleep(0.5)
            self.log.info(f"Power Pump 1 at {power}%")
            self.pump1.get_flow()
            self.log.info(f"Flow Pump 1: {self.pump1.flow:.2f} L/min")
        elif number == 2:
            self.pump2.set_power(power)
            time.sleep(0.5)
            self.log.info(f"Power Pump 2 at {power}%")
            self.pump2.get_flow()
            self.log.info(f"Flow Pump 2: {self.pump2.flow:.2f} L/min")
    @safe_call    
    def get_flow_pump(self, number):
        if number == 1:
            self.pump1.get_flow()
            self.log.info(f"Flow Pump 1: {self.pump1.flow:.2f} L/min", )
        elif number == 2:
            self.pump2.get_flow()
            self.log.info(f"Flow Pump 2: {self.pump2.flow:.2f} L/min")
    #Heater#
    @safe_call
    def set_power_heater1(self, pwm):
        self.heater1.set_pwm(pwm)
        # Assuming max power is 40W for the log calculation
        self.log.info("Heater 1 set to %.0f W", (pwm * 40) / 100)
    @safe_call
    def get_temperatures_heater1(self):
        self.heater1.get_temperatures()
        temp_heater1_in = self.heater1.temp_in
        temp_heater1_out = self.heater1.temp_out
        self.log.info(f"Temperatures Heater 1: Inlet H1={temp_heater1_in:.2f} °C, Outlet H1={temp_heater1_out:.2f} °C")
    @safe_call
    def set_power_heater2(self, pwm):
        self.heater2.set_pwm(pwm)
        # Assuming max power is 40W for the log calculation
        self.log.info("Heater 2 set to %.0f W", (pwm * 40) / 100)
    @safe_call
    def get_temperatures_heater2(self):
        self.heater2.get_temperatures()
        temp_heater2_out = self.heater2.temp_out
        self.log.info(f"Temperatures Heater 2: Outlet H2={temp_heater2_out:.2f} °C")
    #Valvulas (Valves)#
    @safe_call
    def set_open_valve(self, number):
        self.valves.open_valve(number)
        self.log.info("Valve %d opened", number)
    @safe_call
    def set_close_valve(self, number):
        self.valves.close_valve(number)
        self.log.info("Valve %d closed", number)
    @safe_call
    def get_flows_valves(self):
        self.valves.get_flows_and_status()
        # Only show flow if valve is opened, otherwise 0
        flow_valve1_out = self.valves.flow_valve1_out if self.valves.state_valve1 else 0.0
        flow_valve2_out = self.valves.flow_valve2_out if self.valves.state_valve2 else 0.0
        self.log.info("Flow Valve 1: %.2f L/min, Flow Valve 2: %.2f L/min", flow_valve1_out, flow_valve2_out)
    #Estanque (Tank)#
    @safe_call
    def get_level_tank(self):
        self.tank.get_level()
        level_tank = self.tank.level
        self.log.info("Current level: %.1f cm", level_tank)
    @safe_call
    def get_temperatures_tank(self):
        self.tank.get_temperatures()
        temp_tank_bottom = self.tank.temp_bottom
        temp_tank_top = self.tank.temp_top
        self.log.info("Temperatures Tank: Bottom=%.2f °C, Top=%.2f °C", temp_tank_bottom, temp_tank_top)
    #Radiator#
    @safe_call
    def set_power_radiator1(self, power):
        self.radiator1.set_pwm(power)
        self.log.info(f"PWM fan of radiator set to {self.radiator1.power}%")
    @safe_call
    def get_temperatures_radiator1(self):
        self.radiator1.get_temperatures()
        temp_radiator1_in = self.radiator1.temp_in
        temp_radiator1_out = self.radiator1.temp_out
        self.log.info(f"Temperatures Radiator 1: Inlet R1={temp_radiator1_in:.2f} °C, Outlet R1={temp_radiator1_out:.2f} °C")

    #Utilidades (Utilities)#
    def stop(self):
        print("Stop the Loop")
        print("Apagado de emergencia (Emergency Shutdown)")
        # All set_power/set_close methods now correctly use the driver layer,
        # which utilizes the fixed i2c_base.py (prevents bus lock-up).
        self.set_power_pump(1, 0)
        self.set_power_pump(2, 0)
        self.set_power_heater1(0)
        self.set_power_heater2(0)
        self.set_close_valve(1)
        self.set_close_valve(2)
        self.set_power_radiator1(0)
    def update_status(self):
        # All get_flow/get_temperatures methods now correctly return 
        # actual values or 0.0/safe defaults, preventing TypeErrors.
        self.get_flow_pump(1)
        self.get_flow_pump(2)
        self.get_flows_valves()
        self.get_temperatures_heater1()
        self.get_temperatures_heater2()
        self.get_temperatures_tank()
        self.get_temperatures_radiator1()
        self.get_level_tank()
        if self.errors:
            return False #if there is an error in dict
        return True

    # --- Debug function for raw pump/valve data ---
    def debug_flows(self):
        """Debug only: Prints raw values and calculated flows"""
        # Pump 1
        try:
            raw1 = self.pump1.last_raw_bytes if hasattr(self.pump1, "last_raw_bytes") else None
            print(f"[DEBUG] Pump 1 raw bytes: {raw1}, flow property: {self.pump1.flow:.2f} L/min")
        except Exception as e:
            print(f"[DEBUG] Pump 1 error reading raw bytes: {e}")
        # Pump 2
        try:
            raw2 = self.pump2.last_raw_bytes if hasattr(self.pump2, "last_raw_bytes") else None
            print(f"[DEBUG] Pump 2 raw bytes: {raw2}, flow property: {self.pump2.flow:.2f} L/min")
        except Exception as e:
            print(f"[DEBUG] Pump 2 error reading raw bytes: {e}")
        # Valve 1
        try:
            raw_v1 = self.valves.last_raw_bytes_valve1 if hasattr(self.valves, "last_raw_bytes_valve1") else None
            flow_v1 = self.valves.flow_valve1_out if self.valves.state_valve1 else 0.0
            print(f"[DEBUG] Valve 1 raw bytes: {raw_v1}, flow property: {flow_v1:.2f} L/min")
        except Exception as e:
            print(f"[DEBUG] Valve 1 error reading raw bytes: {e}")
        # Valve 2
        try:
            raw_v2 = self.valves.last_raw_bytes_valve2 if hasattr(self.valves, "last_raw_bytes_valve2") else None
            flow_v2 = self.valves.flow_valve2_out if self.valves.state_valve2 else 0.0
            print(f"[DEBUG] Valve 2 raw bytes: {raw_v2}, flow property: {flow_v2:.2f} L/min")
        except Exception as e:
            print(f"[DEBUG] Valve 2 error reading raw bytes: {e}")

    def update_status_dict(self):
        status_ok = self.update_status()
        if not status_ok:
            return False, self.errors
        now = datetime.now()
        self.status_dict = {
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'power_pump1_%': self.pump1.power,
            'flow_pump1_L/min': round(self.pump1.flow, 2),
            'power_heater1_%': self.heater1.power,
            'power_heater1_W': round((self.heater1.power * 40) / 100, 2),
            'temp_heater1_in_°C': round(self.heater1.temp_in, 2),
            'temp_heater1_out_°C': round(self.heater1.temp_out, 2),
            'power_heater2_%': self.heater2.power,
            'power_heater2_W': round((self.heater2.power * 40) / 100, 2),
            'temp_heater2_out_°C': round(self.heater2.temp_out, 2),            
            'valve1_state': 'open' if self.valves.state_valve1 else 'closed',
            'flow_valve1_out_L/min': round(self.valves.flow_valve1_out, 2),
            'valve2_state': 'open' if self.valves.state_valve2 else 'closed',
            'flow_valve2_out_L/min': round(self.valves.flow_valve2_out, 2),
            'level_tank_cm': round(self.tank.level, 1),
            'temp_tank_bottom_°C': round(self.tank.temp_bottom, 2),
            'temp_tank_top_°C': round(self.tank.temp_top, 2),
            'power_pump2_%': self.pump2.power,
            'flow_pump2_L/min': round(self.pump2.flow, 2),
            'power_radiator1_%': self.radiator1.power,
            'power_radiator1_W': round((self.radiator1.power * 40) / 100, 2),
            'temp_radiator1_in_°C': round(self.radiator1.temp_in, 2),
            'temp_radiator1_out_°C': round(self.radiator1.temp_out, 2)
        }
        return True, self.status_dict
    def update_status_dict_mqtt(self):
        status_ok = self.update_status()
        if not status_ok:
            return False, self.errors
        self.mqtt_dict = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pump1': {
                'duty': self.pump1.power,
                'flow': round(self.pump1.flow, 2),
            },
            'pump2':{
                'duty': self.pump2.power,
                'flow': round(self.pump2.flow, 2),
            },
            'heater1':{
                'duty':  self.heater1.power,
                'power': round((self.heater1.power * 40) / 100, 2),
                'temp_in': round(self.heater1.temp_in, 2),
                'temp_out': round(self.heater1.temp_out, 2),
            },
            'heater2':{
                'duty': self.heater2.power,
                'power': round((self.heater2.power * 40) / 100, 2),
                'temp_out': round(self.heater2.temp_out, 2),
            },
            'valves':{
                'valve1_state': 1 if self.valves.state_valve1 else 0,
                'valve2_state': 1 if self.valves.state_valve2 else 0,
                'flow_valve1_out': round(self.valves.flow_valve1_out, 2),
                'flow_Valve2_out': round(self.valves.flow_valve2_out, 2),
            },
            'tank':{
                'level':round(self.tank.level, 1),
                'temp_bottom': round(self.tank.temp_bottom, 2),
                'temp_top': round(self.tank.temp_top, 2),
            },
            'radiator1':{
                'duty': self.radiator1.power,
                'temp_in': round(self.radiator1.temp_in, 2),
                'temp_out': round(self.radiator1.temp_out, 2)
            }
        }
        return True, self.mqtt_dict

    def print_status(self):
        self.update_status()
        print(f"Power pump1: {self.pump1.power}%")
        print(f"Flow pump1: {self.pump1.flow} L/min")
        print(f"Power pump2: {self.pump2.power}%")
        print(f"Flow pump2: {self.pump2.flow} L/min")
        print(f"Power heater1: {self.heater1.power}%")
        print(f"Power heater2: {self.heater2.power}%")
        print(f"Temp heater1 in: {self.heater1.temp_in:.2f}°C")
        print(f"Temp heater1 out: {self.heater1.temp_out:.2f}°C")
        print(f"Temp heater2 out: {self.heater2.temp_out:.2f}°C")
        print(f"State valve 1: {'open' if self.valves.state_valve1 else 'closed'}")
        print(f"State valve 2: {'open' if self.valves.state_valve2 else 'closed'}")
        print(f"Flow valve 1: {self.valves.flow_valve1_out} L/min")
        print(f"Flow valve 2: {self.valves.flow_valve2_out} L/min")
        print(f"Level Tank: {self.tank.level} cm")
        print(f"Temp tank bottom #3: {self.tank.temp_bottom:.2f}°C")
        print(f"Temp tank top #4: {self.tank.temp_top:.2f}°C")
        print(f"Status: {'NOT OK' if self.errors else 'OK'}")

    def append_to_data_log(self, folder_path="./test_data"):
            """Collects the current data and stores it for export (e.g., CSV)"""
            self.update_status()
            # Collect real sensor data
            _, data_point = self.update_status_dict()
            self.data_log.append(data_point)
            self.log.info(f"Colected data: {data_point['timestamp']} - Total: {len(self.data_log)} points")
    def export_to_csv(self, folder_path="./test_data"):
            """Exports data as an Excel file (CSV)"""
            import os
            import pandas as pd
            from datetime import datetime
            if not self.data_log:
                print("There is no data to export!")
                return
            os.makedirs(folder_path, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"solarloop_test_{timestamp}.csv"
            filepath = os.path.join(folder_path, filename)
            df = pd.DataFrame(self.data_log)
            df.to_csv(filepath, index=False, sep=';', decimal=',', encoding='utf-8-sig')
            self.log.info(f"All data exported: {filepath}")
            print(f"[CSV] data successfully saved to '{filepath}' ({len(self.data_log)} points)")
            return filepath
    def clear_data_log(self):
            """Clears the current data log"""
            count = len(self.data_log)
            self.data_log.clear()
            self.log.info(f"Data log cleared. {count} points removed")
            print(f"Data log cleared: {count} points removed")
    def get_data_summary(self):
            """Gives a summary of data collected"""
            if not self.data_log:
                return "There is no data collected"
            first_time = self.data_log[0]['timestamp']
            last_time = self.data_log[-1]['timestamp']
            count = len(self.data_log)
            summary = f"""
            === Data Summary ===
            Total points: {count}
            First registration: {first_time}
            Last registration: {last_time}
            ========================
            """
            return summary
if __name__ == "__main__":
    loop = Loop(
        pump = Pump(device_key="PUMP1_SOLAR_LOOP"),
        valves = Valve(device_key="VALVES"),
        heater1 = Heater(device_key="HEATER1_SOLAR_LOOP"),
        heater2 = Heater(device_key="HEATER2_SOLAR_LOOP"),
        tank = Tank(device_key="HEAT_STORAGE"),
        radiator1 = Radiator(device_key="RADIATOR_PROCESS_LOOP"),
        verbose= True
    )
    # Clear any previous data log
    loop.clear_data_log()
    # Activate necessary components
    loop.set_open_valve(1)              # open valve 1
    loop.set_power_pump(1, 100)          # Start pump x at x %
    loop.set_power_pump(2, 100)          # Start pump x at x %
    #loop.set_power_heater1(0)          # start heater 1 at x %
    print("Heater1 PWM:", loop.heater1.power)
    #loop.set_power_heater2(100)          # start heater 2 at x %
    loop.set_power_radiator1(100)        # start radiator 1 at x %
    loop.debug_flows()   # <-- raw values of the pumps / valves
    loop.print_status()
    print("System activated.")
    # Save start time
    start_time = time.monotonic()
    total_duration = 1 * 60 # hours * min * seconds
    next_sample = start_time
    try:
        while time.monotonic() - start_time < total_duration:
            now = time.monotonic()
            # If 20 seconds have passed since the last sample (total duration is 60s, sampled every 20s)
            if now >= next_sample:
                loop.append_to_data_log()  # save current data
                minutos_transcurridos = int((now - start_time) // 60)
                print(f"Sample {minutos_transcurridos + 1}/30 registrated.")
                next_sample += 20  # Next sample every 20 seconds
            time.sleep(1)  # Sleep for 1 second to avoid overloading the processor
    except KeyboardInterrupt:
        print("Measurement interrupted manually by the user.")
    # Stop all devices
    loop.stop()
    loop.append_to_data_log()  # save final state
    print("System stopped. Final sample recorded.")
    # Show summary and export to Excel
    print(loop.get_data_summary())
    loop.export_to_csv()