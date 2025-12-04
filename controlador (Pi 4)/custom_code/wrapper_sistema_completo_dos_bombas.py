import time
from datetime import datetime
import pandas as pd
from bomba_i2c import Pump    
from valvulas_i2c import Valves    
from calentador_i2c import Heater1
from estanque_i2c import Tank
from disipador_i2c import Radiator1
from calentador_dos_i2c import Heater2

shared_data_log = []

def clear_data_log():
    global shared_data_log
    shared_data_log = []

def export_to_csv():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"test_data/both_loops_{timestamp}.csv"
    df = pd.DataFrame(shared_data_log)
    df.to_csv(filename, index=False, sep=';', decimal=',', encoding='utf-8-sig')


    print(f"[CSV] Data successfully saved to '{filename}'")
    return filename

class SolarLoop:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.pump1 = Pump(address=0x10)
        self.heater1 = Heater1()
        self.heater2 = Heater2()
        self.valves = Valves()
        self.tank = Tank()


    def stop(self):
        self.power_pump1(0)
        self.power_heater1(0)
        self.power_heater2(0)
        
    def power_pump1(self, value):
        self.pump1.set_power(value)

    def power_heater1(self, value):
        self.heater1.set_pwm_heater1(value)

    def power_heater2(self, value):
        self.heater2.set_pwm_heater2(value)

    def open_valve(self, num):
        if num == 1:
            self.valves.open_valve(1)
        elif num == 2:
            self.valves.open_valve(2)

    def close_valve(self, num):
        if num == 1:
            self.valves.close_valve(1)
        elif num == 2:
            self.valves.close_valve(2)

    def append_to_data_log(self, timestamp):
        self.pump1.get_flow()
        time.sleep(0.1)
        self.heater1.get_temperatures()
        time.sleep(0.1)
        self.heater2.get_temperatures()
        time.sleep(0.5)

        self.valves.get_flows()
        time.sleep(0.1)
        self.tank.get_level()
        time.sleep(0.1)
        self.tank.get_temperatures() 

        now = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

        # Try to find existing entry at this timestamp
        existing_entry = next((d for d in shared_data_log if d["timestamp"] == timestamp), None)

        data = {
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'timestamp': timestamp,
            'power_pump1_%': self.pump1.power,
            'flow_pump1_L/min': round(self.pump1.flow, 2),
            'power_heater1_%': self.heater1.power,
            'power_heater1_W': round((self.heater1.power * 40) / 100, 2),
            'temp_heater1_in_°C': round(self.heater1.temp_in, 2),
            'temp_heater1_out_°C': round(self.heater1.temp_out, 2),
            'power_heater2_%': self.heater2.power,
            'power_heater2_W': round((self.heater2.power * 40) / 100, 2),
            'temp_heater2_out_°C': round(self.heater2.temp_out, 2),
            'valve1_status': 'open' if self.valves.state_valve1 else 'close',
            'flow_valve1_out_L/min': round(self.valves.flow_valve1_out, 2),
            'valve2_status': 'open' if self.valves.state_valve2 else 'close',
            'flow_valve2_out_L/min': round(self.valves.flow_valve2_out, 2),
            'level_tank_cm': round(self.tank.level, 1),
            'temp_tank_bottom_°C': round(self.tank.temp_bottom, 2),
            'temp_tank_top_°C': round(self.tank.temp_top, 2)
        }

        if existing_entry:
            existing_entry.update(data)
        else:
            shared_data_log.append(data)

        if self.verbose:
            print("[SolarLoop] Logged data point.")

    # ---------- NEUE (ERSATZ-)FUNKTION: zeitbasierte Steuerung ----------
    def run_synchronized_test(self, process_loop, duration_minutes, interval_seconds):
        start_time = time.time()
        end_time = start_time + duration_minutes * 60
        next_time = start_time  # Zeitpunkt der nächsten Messung
        i = 0

        print(f"[SYNC] Starting synchronized test for {duration_minutes} minutes (interval {interval_seconds}s)")

        while time.time() < end_time:
            now = datetime.now()
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

            # Messung SolarLoop
            self.append_to_data_log(timestamp)
            time.sleep(0.1)  # kurzer Puffer

            # Messung ProcessLoop
            process_loop.append_to_data_log(timestamp)

            i += 1
            if self.verbose or process_loop.verbose:
                print(f"[SYNC] Measurement {i} at {timestamp}")

            # Berechne den exakten Zeitpunkt für die nächste Messung
            next_time += interval_seconds
            sleep_time = max(0, next_time - time.time())  # falls Messungen länger dauern als Interval, sofort weitermachen
            if sleep_time > 0:
                time.sleep(sleep_time)

# ----------------------------------------------------------------


class ProcessLoop:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.pump2 = Pump(address=0x14)
        self.radiator1 = Radiator1()


    def stop(self):
        self.power_pump2(0)
        self.power_radiator1(0)

    def power_pump2(self, value):
        self.pump2.set_power(value)

    def power_radiator1(self, value):
        self.radiator1.set_pwm_fan(value)

    def append_to_data_log(self, timestamp):
        self.pump2.get_flow()  # Damit du auch die Pumpe im ProcessLoop abfragst
        time.sleep(0.1)
        self.radiator1.get_temperatures()
        
        now = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

        existing_entry = next((d for d in shared_data_log if d["timestamp"] == timestamp), None)

        data = {
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'timestamp': timestamp,
            'power_pump2_%': self.pump2.power,
            'flow_pump2_L/min': round(self.pump2.flow, 2),
            'radiator_power_%': self.radiator1.power,
            'temp_radiator1_in_°C': round(self.radiator1.temp_in, 2),
            'temp_radiator1_out_°C': round(self.radiator1.temp_out, 2)
        }

        if existing_entry:
            existing_entry.update(data)
        else:
            shared_data_log.append(data)

        if self.verbose:
            print("[ProcessLoop] Logged data point.")

    def run_test(self, duration_minutes, interval_seconds):
        total = (duration_minutes * 60) // interval_seconds
        for _ in range(total):
            now = datetime.now()
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            self.append_to_data_log(timestamp)
            time.sleep(interval_seconds)
