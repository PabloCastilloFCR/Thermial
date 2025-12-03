import time
from datetime import datetime
import pandas as pd


from modulo_bomba_flujometro import Bomba    
from modulo_valvulas_loop_termico import Valvulas    
from modulo_calentador_loop_termico import Calentador
from modulo_estanque_loop_termico import Estanque
from modulo_dissipador_loop_proceso import Dissipador

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
        self.bomba = Bomba()

        self.calentador = Calentador()
        self.valvulas = Valvulas()
        self.estanque = Estanque()

    def stop(self):
        self.potencia_bomba(0)
        self.potencia_calentador(0)

    def potencia_bomba(self, value):
        self.bomba.set_potencia(value)

    def potencia_calentador(self, value):
        self.calentador.set_pwm_calentador(value)

    def abrir_valvula(self, num):
        if num == 1:
            self.valvulas.abrir_valvula(1)
        elif num == 2:
            self.valvulas.abrir_valvula(2)

    def append_to_data_log(self, timestamp):
        self.bomba.get_flujo()
        self.calentador.get_temperaturas()
        self.valvulas.get_flujos()
        self.estanque.get_nivel()
        self.estanque.get_temperaturas() 

        now = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

        # Try to find existing entry at this timestamp
        existing_entry = next((d for d in shared_data_log if d["Timestamp"] == timestamp), None)

        data = {
            'Fecha': now.strftime('%Y-%m-%d'),
            'Hora': now.strftime('%H:%M:%S'),
            'Timestamp': timestamp,
            'Bomba_Potencia_%': self.bomba.potencia,
            'Bomba_Flujo_L/min': round(self.bomba.flujo, 2),
            'Calentador_Potencia_%': self.calentador.potencia,
            'Calentador_Potencia_W': round((self.calentador.potencia * 40) / 100, 2),
            'Temp_1_Entrada_°C': round(self.calentador.temp1, 2),
            'Temp_2_Salida_°C': round(self.calentador.temp2, 2),
            'Valvula1_Estado': 'Abierta' if self.valvulas.state_valve1 else 'Cerrada',
            'Valvula2_Estado': 'Abierta' if self.valvulas.state_valve2 else 'Cerrada',
            'Valvula1_Flujo_L/min': round(self.valvulas.flow1, 2),
            'Valvula2_Flujo_L/min': round(self.valvulas.flow2, 2),
            'Nivel_Estanque_cm': round(self.estanque.nivel, 1),
            'Estanque_Temp3_°C': round(self.estanque.temp3, 2),
            'Estanque_Temp4_°C': round(self.estanque.temp4, 2)
        }

        if existing_entry:
            existing_entry.update(data)
        else:
            shared_data_log.append(data)

        if self.verbose:
            print("[SolarLoop] Logged data point.")

    def run_synchronized_test(self, process_loop, duration_minutes, interval_seconds):
        total_measurements = (duration_minutes * 60) // interval_seconds
        print(f"[SYNC] Iniciando mediciones por {duration_minutes} minutos (cada {interval_seconds} segundos)...")
        print(f"[SYNC] Total de mediciones esperadas: {total_measurements}")

        for i in range(total_measurements):
            now = datetime.now()
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

            self.append_to_data_log(timestamp)
            process_loop.append_to_data_log(timestamp)

            if self.verbose or process_loop.verbose:
                print(f"[SYNC] Logged data at {timestamp}")

            print(f"[SYNC] Medición {i+1}/{total_measurements} completada a las {now.strftime('%H:%M:%S')}")
            time.sleep(interval_seconds)

class ProcessLoop:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.dissipador = Dissipador()


    def stop(self):
        self.potencia_dissipador(0)

    def potencia_dissipador(self, value):
        self.dissipador.set_pwm_ventilador(value)

    def append_to_data_log(self, timestamp):
        self.dissipador.get_temperaturas()
        
        now = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

        existing_entry = next((d for d in shared_data_log if d["Timestamp"] == timestamp), None)

        data = {
            'Fecha': now.strftime('%Y-%m-%d'),
            'Hora': now.strftime('%H:%M:%S'),
            'Timestamp': timestamp,
            'Dissipador_Potencia_%': self.dissipador.potencia,
            'Dissipador_Temp5_°C': round(self.dissipador.temp5, 2),
            'Dissipador_Temp6_°C': round(self.dissipador.temp6, 2)
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
