# --- Imports der Module ---
import logging
from bomba_i2c import Bomba    
from valvulas_i2c import Valvulas    
from calentador_i2c import Calentador
from estanque_i2c import Estanque
from disipador_i2c import Disipador
import time
import pandas as pd
from datetime import datetime
import os


# ---------------------------------------------------------------------
# One-time configuration (e.g. in your main script)
# ---------------------------------------------------------------------
logger = logging.getLogger("solarloop")          # choose a namespace for your module
handler = logging.StreamHandler()           # print to stdout
fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
handler.setFormatter(logging.Formatter(fmt))
logger.addHandler(handler)

# Toggle verbosity here:
logger.setLevel(logging.INFO)    # verbose: INFO, DEBUG
# logger.setLevel(logging.WARNING)  # quiet: WARNING, ERROR, CRITICAL
#Comentario de prueba

class SolarLoop:
    """
    Controlador de lazo solar con bomba, válvulas, calentador y tanque.
    Todos los mensajes van al logger 'solarloop'. Verbose = nivel INFO.
    """

    def __init__(self, bomba = Bomba, valvulas = Valvulas, calentador = Calentador, estanque =  Estanque, verbose = False):
        self.bomba = Bomba()
        self.valvulas = Valvulas()
        self.calentador = Calentador()
        self.estanque = Estanque()
        self.data_log = []  # Nueva lista para almacenar datos

        # Si el usuario quiere verbosidad, baja el umbral del logger
        if verbose:
            logging.getLogger("solarloop").setLevel(logging.INFO)
        else:
            logging.getLogger("solarloop").setLevel(logging.WARNING)

        self.log = logging.getLogger("solarloop")

    def potencia_bomba(self, potencia, verbose = False):
        """
        potencia: entero de 0 a 100. Solo numero.
        """
        self.bomba.set_potencia(potencia)
        self.log.info("Potencia de la bomba a %d%%", self.bomba.potencia)
        
    def obtener_flujo_bomba(self, verbose = False):
        self.bomba.get_flujo()
        self.log.info("Flujo bomba: %.2f L/min", self.bomba.flujo)
    
    def potencia_calentador(self, pwm):
        self.calentador.set_pwm_calentador(pwm)
        self.log.info("Calentador seteado a %.0f W", (pwm * 40) / 100)
    
    def obtener_temperaturas_calentador(self):
        self.calentador.get_temperaturas()
        t1 = self.calentador.temp1
        t2 = self.calentador.temp2
        self.log.info("Temperaturas calentador: Entrada=%.2f °C, Salida=%.2f °C",
                      t1, t2)
    
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
        print(f"Flujo Bomba: {self.bomba.flujo} L/min")
        print(f"Potencia Calentador: {self.calentador.potencia}%")
        print(f"Temperatura 1: {self.calentador.temp1:.2f}°C")
        print(f"Temperatura 2: {self.calentador.temp2:.2f}°C")
        print(f"Estado Valvula 1: {'Abierta' if self.valvulas.state_valve1 else 'Cerrada'}")
        print(f"Estado Valvula 2: {'Abierta' if self.valvulas.state_valve2 else 'Cerrada'}")
        print(f"Flujo Valvula 1: {self.valvulas.flow1} L/min")
        print(f"Flujo Valvula 2: {self.valvulas.flow2} L/min")
        print(f"Nivel Estanque: {self.estanque.nivel} cm")
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

        #obtener fecha y hora actuales
        now = datetime.now()
        # Colectar datos reales de los sensores
        data_point = {
            'Fecha': now.strftime('%Y-%m-%d'),
            'Hora': now.strftime('%H:%M:%S'), 
            #'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
    
        self.data_log.append(data_point)
        self.log.info(f"Datos colectados: {data_point['Fecha']} {data_point['Hora']}  - Total: {len(self.data_log)} puntos")

    def export_to_excel(self, folder_path="./test_data"):
        """Exporta los datos colectados a CSV"""
        if not self.data_log:
            print("No datos para exportar!")
            return
        
        os.makedirs(folder_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"solarloop_test_{timestamp}.csv"
        filepath = os.path.join(folder_path, filename)

        df = pd.DataFrame(self.data_log)
        df.to_csv(filepath, index=False, sep=';', decimal=',')

        self.log.info(f"Todos los datos exportados: {filepath}")
        print(f"Excel hecho con {len(self.data_log)} datos: {filepath}")
        return filepath
    
    def save_to_excel(self, folder_path="./test_data"):
        """Alias para export_to_excel"""
        return self.export_to_excel(folder_path)
    
    def clear_data_log(self):
        """Limpia el log de datos actual"""
        count = len(self.data_log)
        self.data_log.clear()
        self.log.info(f"Log de datos limpiado. {count} puntos eliminados")
        print(f"Log limpiado: {count} puntos eliminados")

    def get_data_summary(self):
        """Retorna un resumen de los datos colectados"""
        if not self.data_log:
            return "No hay datos colectados"
        
        first_time = self.data_log[0]['Timestamp']
        last_time = self.data_log[-1]['Timestamp']
        count = len(self.data_log)

        summary = f"""
=== RESUMEN DE DATOS DEL SOLAR LOOP===
Total de puntos: {count}
Primer registro: {first_time}
Último registro: {last_time}
========================
        """
        return summary
    
    def run_test(self, duracion_minutos, intervalo_segundos=30):
        """Duración del test"""
        print(f"DEBUG: duracion_minutos={duracion_minutos}, intervalo_segundos={intervalo_segundos}")
        total_mediciones = (duracion_minutos * 60) // intervalo_segundos
        print(f"DEBUG: total_mediciones = ({duracion_minutos} * 60) // {intervalo_segundos} = {total_mediciones}")
        
        print(f"Iniciando mediciones por {duracion_minutos} minutos (cada {intervalo_segundos} segundos)...")
        
        for i in range(total_mediciones):
            time.sleep(intervalo_segundos)
            self.update_status()
            self.append_to_data_log()
            print(f"Medición {i+1}/{total_mediciones} completada")

if __name__ == "__main__":
    loop = SolarLoop(
        bomba = Bomba(),
        valvulas = Valvulas(),
        calentador = Calentador(),
        estanque = Estanque(),
        verbose= True
    )

    # Limpiar cualquier log anterior de datos
    loop.clear_data_log()

    # Activar componentes necesarios
    loop.abrir_valvula(1)              # Abrir válvula 1
    loop.potencia_bomba(80)            # Encender bomba al 70%
    loop.potencia_calentador(75)       # Encender calentador al 60%

    print("Sistema activado. Iniciando registro de datos por 30 minutos (1 muestra por minuto)...")

    # Guardar el tiempo de inicio
    tiempo_inicio = time.monotonic()
    duracion_total = 30 * 60  # 30 minutos en segundos
    proxima_muestra = tiempo_inicio

    try:
        while time.monotonic() - tiempo_inicio < duracion_total:
            ahora = time.monotonic()

            # Si ha pasado un minuto desde la última muestra
            if ahora >= proxima_muestra:
                loop.append_to_data_log()  # Guardar datos actuales
                minutos_transcurridos = int((ahora - tiempo_inicio) // 60)
                print(f"Muestra {minutos_transcurridos + 1}/30 registrada.")
                proxima_muestra += 60  # Programar siguiente muestra en 60 segundos

            time.sleep(1)  # Dormir 1 segundo para no saturar el procesador

    except KeyboardInterrupt:
        print("Medición interrumpida manualmente por el usuario.")

    # Detener todos los dispositivos
    loop.stop()
    loop.append_to_data_log()  # Guardar estado final
    print("Sistema detenido. Muestra final registrada.")

    # Mostrar resumen y exportar a Excel
    print(loop.get_data_summary())
    loop.export_to_excel()


