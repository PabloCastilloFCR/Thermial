# --- Mock-Klassen für Simulation ohne Hardware ---
import logging
import time
import pandas as pd
from datetime import datetime
import os
import random

# Mock-Klassen die das Verhalten der echten Hardware simulieren
class MockBomba:
    def __init__(self):
        self.potencia = 0
        self.flujo = 0.0
    
    def set_potencia(self, potencia):
        self.potencia = max(0, min(100, potencia))
        # Simuliere Flujo basierend auf Potencia
        self.flujo = self.potencia * 0.5 + random.uniform(-2, 2)
        if self.flujo < 0:
            self.flujo = 0
    
    def get_flujo(self):
        # Füge etwas Rauschen hinzu
        noise = random.uniform(-0.5, 0.5)
        self.flujo = max(0, self.flujo + noise)

class MockValvulas:
    def __init__(self):
        self.state_valve1 = False
        self.state_valve2 = False
        self.flow1 = 0.0
        self.flow2 = 0.0
    
    def abrir_valvula(self, numero):
        if numero == 1:
            self.state_valve1 = True
        elif numero == 2:
            self.state_valve2 = True
    
    def cerrar_valvula(self, numero):
        if numero == 1:
            self.state_valve1 = False
            self.flow1 = 0.0
        elif numero == 2:
            self.state_valve2 = False
            self.flow2 = 0.0
    
    def get_flujos(self):
        # Simuliere Flujo nur wenn Ventil offen ist
        if self.state_valve1:
            self.flow1 = random.uniform(15, 25)
        if self.state_valve2:
            self.flow2 = random.uniform(10, 20)

class MockCalentador:
    def __init__(self):
        self.potencia = 0
        self.temp1 = 20.0  # Eingangstemperatur
        self.temp2 = 20.0  # Ausgangstemperatur
    
    def set_pwm_calentador(self, pwm):
        self.potencia = max(0, min(100, pwm))
    
    def get_temperaturas(self):
        # Simuliere realistische Temperaturen
        base_temp = 22 + random.uniform(-2, 2)
        self.temp1 = base_temp
        # Ausgangstemperatur höher wenn Heizer an
        temp_increase = self.potencia * 0.3
        self.temp2 = base_temp + temp_increase + random.uniform(-1, 1)

class MockEstanque:
    def __init__(self):
        self.nivel = 50.0  # cm
        self.temp3 = 20.0
        self.temp4 = 20.0
    
    def get_nivel(self):
        # Simuliere leichte Schwankungen im Wasserpegel
        self.nivel += random.uniform(-0.5, 0.5)
        self.nivel = max(10, min(80, self.nivel))
    
    def get_temperaturas(self):
        # Simuliere Tank-Temperaturen
        self.temp3 = 25 + random.uniform(-3, 3)
        self.temp4 = 26 + random.uniform(-3, 3)

# ---------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------
logger = logging.getLogger("solarloop")
handler = logging.StreamHandler()
fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
handler.setFormatter(logging.Formatter(fmt))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class SolarLoopTest:
    """
    Test-Version des SolarLoop Controllers mit Mock-Hardware
    """

    def __init__(self, verbose=True):
        # Verwende Mock-Klassen statt echter Hardware
        self.bomba = MockBomba()
        self.valvulas = MockValvulas()
        self.calentador = MockCalentador()
        self.estanque = MockEstanque()
        self.data_log = []

        if verbose:
            logging.getLogger("solarloop").setLevel(logging.INFO)
        else:
            logging.getLogger("solarloop").setLevel(logging.WARNING)
        self.log = logging.getLogger("solarloop")

    def potencia_bomba(self, potencia):
        self.bomba.set_potencia(potencia)
        self.log.info("Potencia de la bomba a %d%%", self.bomba.potencia)
        
    def obtener_flujo_bomba(self):
        self.bomba.get_flujo()
        self.log.info("Flujo bomba: %.2f L/min", self.bomba.flujo)
    
    def potencia_calentador(self, pwm):
        self.calentador.set_pwm_calentador(pwm)
        self.log.info("Calentador seteado a %.0f W", (pwm * 40) / 100)
    
    def obtener_temperaturas_calentador(self):
        self.calentador.get_temperaturas()
        t1 = self.calentador.temp1
        t2 = self.calentador.temp2
        self.log.info("Temperaturas calentador: Entrada=%.2f °C, Salida=%.2f °C", t1, t2)
    
    def abrir_valvula(self, numero):
        self.valvulas.abrir_valvula(numero)
        self.log.info("Válvula %d abierta", numero)

    def cerrar_valvula(self, numero):
        self.valvulas.cerrar_valvula(numero)
        self.log.info("Válvula %d cerrada", numero)

    def obtener_flujos_valvulas(self):
        self.valvulas.get_flujos()
        f1 = self.valvulas.flow1
        f2 = self.valvulas.flow2
        self.log.info("Flujo 1: %.2f L/min, Flujo 2: %.2f L/min", f1, f2)

    def obtener_nivel_estanque(self):
        self.estanque.get_nivel()
        nivel_valor = self.estanque.nivel
        self.log.info("Nivel actual: %.1f cm", nivel_valor)

    def obtener_temperaturas_estanque(self):
        self.estanque.get_temperaturas()
        t3 = self.estanque.temp3
        t4 = self.estanque.temp4
        self.log.info("Temperaturas estanque: T3=%.2f °C, T4=%.2f °C", t3, t4)

    def stop(self):
        print("Detención del Loop")
        self.bomba.set_potencia(0)
        self.calentador.set_pwm_calentador(0)
        self.valvulas.cerrar_valvula(1)
        self.valvulas.cerrar_valvula(2)

    def print_status(self):
        self.update_status()
        print(f"Potencia Bomba: {self.bomba.potencia}%")
        print(f"Flujo Bomba: {self.bomba.flujo:.2f} L/min")
        print(f"Potencia Calentador: {self.calentador.potencia}%")
        print(f"Temperatura 1: {self.calentador.temp1:.2f}°C")
        print(f"Temperatura 2: {self.calentador.temp2:.2f}°C")
        print(f"Estado Valvula 1: {'Abierta' if self.valvulas.state_valve1 else 'Cerrada'}")
        print(f"Estado Valvula 2: {'Abierta' if self.valvulas.state_valve2 else 'Cerrada'}")
        print(f"Flujo Valvula 1: {self.valvulas.flow1:.2f} L/min")
        print(f"Flujo Valvula 2: {self.valvulas.flow2:.2f} L/min")
        print(f"Nivel Estanque: {self.estanque.nivel:.1f} cm")
        print(f"Temperatura Estanque #1: {self.estanque.temp3:.2f}°C")
        print(f"Temperatura Estanque #2: {self.estanque.temp4:.2f}°C")
    
    def update_status(self):
        self.obtener_flujo_bomba()
        self.obtener_flujos_valvulas()
        self.obtener_temperaturas_calentador()
        self.obtener_temperaturas_estanque()
        self.obtener_nivel_estanque()

    def append_to_data_log(self, folder_path="./test_data"):
        """Colecta los datos actuales y los guarda para Excel"""
        self.update_status()
    
        # colectar datos
        data_point = {
            'Timestamp': datetime.now().strftime('%H:%M:%S'),
            'Bomba_Potencia_%': self.bomba.potencia,
            'Bomba_Flujo_L/min': round(self.bomba.flujo, 2),
            'Calentador_Potencia_W': self.calentador.potencia * 40,
            'Temp_Entrada_°C': round(self.calentador.temp1, 2),
            'Temp_Salida_°C': round(self.calentador.temp2, 2),
            'Valvula1_Flujo_L/min': round(self.valvulas.flow1, 2),
            'Valvula2_Flujo_L/min': round(self.valvulas.flow2, 2),
            'Nivel_Estanque_cm': round(self.estanque.nivel, 1),
            'Estanque_Temp1_°C': round(self.estanque.temp3, 2),
            'Estanque_Temp2_°C': round(self.estanque.temp4, 2)
        }
    
        self.data_log.append(data_point)
        self.log.info(f"Datos colectados: {data_point['Timestamp']}")

    def export_to_excel(self, folder_path="./test_data"):
        """exporta los datos colectados al Excel"""
        if not self.data_log:
            print("No datos para exportar!")
            return
        
        os.makedirs(folder_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"solarloop_test_{timestamp}.xlsx"
        filepath = os.path.join(folder_path, filename)
        
        df = pd.DataFrame(self.data_log)
        df.to_excel(filepath, index=False)
        
        self.log.info(f"Todos los datos exportados: {filepath}")
        print(f"Excel hecho con {len(self.data_log)} datos: {filepath}")
        return filepath

def run_comprehensive_test():
    """Führt einen umfassenden Test des Systems durch"""
    print("=== SOLARLOOP COMPREHENSIVE TEST ===")
    print("Teste alle Funktionen mit simulierten Daten...\n")
    
    loop = SolarLoopTest(verbose=True)
    
    # Test Scenario 1: Basic Operation
    print("TEST 1: Basic Operation")
    loop.abrir_valvula(1)
    time.sleep(1)
    loop.potencia_bomba(50)
    time.sleep(1)
    loop.potencia_calentador(75)
    time.sleep(2)
    loop.append_to_data_log()  # Speichere erste Messung
    loop.print_status()
    print("\n" + "="*50 + "\n")
    
    # Test Scenario 2: High Power Operation
    print("TEST 2: High Power Operation")
    loop.potencia_bomba(100)
    loop.potencia_calentador(100)
    loop.abrir_valvula(2)
    time.sleep(2)
    loop.append_to_data_log()  # Speichere zweite Messung
    loop.print_status()
    print("\n" + "="*50 + "\n")
    
    # Test Scenario 3: Variable Operation (mehrere Datenpunkte)
    print("TEST 3: Variable Operation (5 Datenpunkte)")
    for i in range(5):
        # Variiere die Parameter
        bomba_power = random.randint(30, 90)
        calentador_power = random.randint(20, 80)
        
        loop.potencia_bomba(bomba_power)
        loop.potencia_calentador(calentador_power)
        
        # Zufällig Ventile öffnen/schließen
        if random.choice([True, False]):
            loop.abrir_valvula(1)
        else:
            loop.cerrar_valvula(1)
            
        time.sleep(1)
        loop.append_to_data_log()
        print(f"Datenpunkt {i+1}/5 gespeichert")
    
    print("\n" + "="*50 + "\n")
    
    # Test Scenario 4: Shutdown
    print("TEST 4: System Shutdown")
    loop.stop()
    time.sleep(1)
    loop.append_to_data_log()  # Finale Messung
    loop.print_status()
    
    # Exportiere alle Daten zu Excel
    print("\n" + "="*50)
    print("EXPORT TO EXCEL")
    filepath = loop.export_to_excel()
    print(f"Test abgeschlossen! Excel-Datei erstellt: {filepath}")
    
    return loop

if __name__ == "__main__":
    # Führe den Test aus
    test_loop = run_comprehensive_test()
    
    # Zeige zusammenfassung der gesammelten Daten
    print(f"\nZusammenfassung: {len(test_loop.data_log)} Datenpunkte gesammelt")
    print("Erste 3 Datenpunkte:")
    for i, data in enumerate(test_loop.data_log[:3]):
        print(f"  {i+1}. {data['Timestamp']}: Bomba {data['Bomba_Potencia_%']}%, Calentador {data['Calentador_Potencia_W']}W")





        