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
logger = logging.getLogger("loop")          # choose a namespace for your module
handler = logging.StreamHandler()           # print to stdout
fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
handler.setFormatter(logging.Formatter(fmt))
logger.addHandler(handler)

# Toggle verbosity here:
logger.setLevel(logging.INFO)    # verbose: INFO, DEBUG
# logger.setLevel(logging.WARNING)  # quiet: WARNING, ERROR, CRITICAL
#Comentario de prueba

class Loop:
    """
    Controlador de lazo solar con bomba, válvulas, calentador y tanque.
    Todos los mensajes van al logger 'solarloop'. Verbose = nivel INFO.
    """
    def __init__(self, 
                 bomba = Bomba, 
                 valvulas = Valvulas, 
                 calentador = Calentador, 
                 estanque =  Estanque,
                 disipador = Disipador, 
                 verbose = False):
        
        self.bomba1 = Bomba(address=0x10)
        self.bomba2 = Bomba(address=0x14)
        self.valvulas = Valvulas()
        self.calentador = Calentador()
        self.estanque = Estanque()
        self.disipador = Disipador()
        self.data_log = []  # Nueva lista para almacenar datos

        # Si el usuario quiere verbosidad, baja el umbral del logger
        if verbose:
            logging.getLogger("loop").setLevel(logging.INFO)
        else:
            logging.getLogger("loop").setLevel(logging.WARNING)

        self.log = logging.getLogger("loop")

    #Bombas#
    def set_potencia_bomba(self, number:int, potencia:int):
        """
        number = 1 o 2. Solo numero.
        potencia: entero de 0 a 100. Solo numero.
        """
        if potencia > 100:
            potencia = 100
        elif potencia < 0:
            potencia = 0

        if number == 1:
            self.bomba1.set_potencia(potencia)
            self.log.info(f"Potencia Bomba 1 a {potencia}%")
        elif number == 2:
            self.bomba2.set_potencia(potencia)
            self.log.info(f"Potencia Bomba 2 a {potencia}%")
        
    def get_flujo_bomba(self, number):
        if number == 1:
            self.bomba1.get_flujo()
            self.log.info(f"Flujo bomba 1: {self.bomba1.flujo:.2f} L/min", )
        elif number == 2:
            self.bomba2.get_flujo()
            self.log.info(f"Flujo bomba 2: {self.bomba2.flujo:.2f} L/min")
    
    #Calentador#
    def set_potencia_calentador(self, pwm):
        self.calentador.set_pwm_calentador(pwm)
        self.log.info("Calentador seteado a %.0f W", (pwm * 40) / 100)
    
    def get_temperaturas_calentador(self):
        self.calentador.get_temperaturas()
        t1 = self.calentador.temp1
        t2 = self.calentador.temp2
        self.log.info(f"Temperaturas calentador: Entrada={t1:.2f} °C, Salida={t2:.2f} °C")
    
    #Valvulas#
    def set_abrir_valvula(self, numero):
        self.valvulas.abrir_valvula(numero)
        self.log.info("Válvula %d abierta", numero)

    def set_cerrar_valvula(self, numero):
        self.valvulas.cerrar_valvula(numero)
        self.log.info("Válvula %d cerrada", numero)

    def get_flujos_valvulas(self):
        self.valvulas.get_flujos()
        f1 = self.valvulas.flow1
        f2 = self.valvulas.flow2
        self.log.info("Flujo 1: %.2f L/min, Flujo 2: %.2f L/min", f1, f2)

    #Estanque#
    def get_nivel(self):
        self.estanque.get_nivel()
        nivel_valor = self.estanque.nivel
        self.log.info("Nivel actual: %.1f cm", nivel_valor)

    def get_temperaturas_estanque(self):
        self.estanque.get_temperaturas()
        t3 = self.estanque.temp3
        t4 = self.estanque.temp4
        self.log.info("Temperaturas estanque: T3=%.2f °C, T4=%.2f °C", t3, t4)
    
    #Disipador#
    def set_potencia_disipador(self, potencia):
        self.disipador.set_pwm_ventilador(potencia)
        self.log.info(f"PWM Disipador a {self.disipador.potencia}%")

    def get_temperaturas_disipador(self):
        self.disipador.get_temperaturas()
        t5 = self.disipador.temp5
        t6 = self.disipador.temp6
        self.log.info(f"Temperaturas disipador: Entrada={t5:.2f} °C, Salida={t6:.2f} °C")


    #Utilidades#
    def stop(self):
        print("Detención del Loop")
        self.bomba1.set_potencia(0)
        self.bomba2.set_potencia(0)
        self.calentador.set_pwm_calentador(0)
        self.disipador.set_pwm_ventilador(0)
        self.valvulas.cerrar_valvula(1)
        self.valvulas.cerrar_valvula(2)
    
    def update_status(self):
        self.get_flujo_bomba(1)
        self.get_flujo_bomba(2)
        self.get_flujos_valvulas()
        self.get_temperaturas_calentador()
        self.get_temperaturas_estanque()
        self.get_temperaturas_disipador()
        self.get_nivel()

    def update_status_dict(self):
        self.update_status()
        self.status_dict = {
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Bomba1_P_%': self.bomba1.potencia,
            'Bomba2_P_%': self.bomba2.potencia,
            'Bomba1_F_L/min': round(self.bomba1.flujo, 2),
            'Bomba2_F_L/min': round(self.bomba2.flujo, 2),
            'Calentador_P_%': self.calentador.potencia,
            'Calentador_P_W': round((self.calentador.potencia * 40) / 100, 2),
            'Calentador_T_1_°C': round(self.calentador.temp1, 2),
            'Calentador_T_2_°C': round(self.calentador.temp2, 2),
            'Valvula1_S': 'Abierta' if self.valvulas.state_valve1 else 'Cerrada',
            'Valvula2_S': 'Abierta' if self.valvulas.state_valve2 else 'Cerrada',
            'Valvula1_F_L/min': round(self.valvulas.flow1, 2),
            'Valvula2_F_L/min': round(self.valvulas.flow2, 2),
            'Estanque_L_cm': round(self.estanque.nivel, 1),
            'Estanque_T3_°C': round(self.estanque.temp3, 2),
            'Estanque_T4_°C': round(self.estanque.temp4, 2),
            'Disipador_P_%': self.disipador.potencia,
            'Disipador_T5_°C': round(self.disipador.temp5, 2),
            'Disipador_T6_°C': round(self.disipador.temp6, 2)
        }
        return self.status_dict
    
    def update_status_dict_mqtt(self):
        self.update_status()
        self.mqtt_dict = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pump1': {
                'duty': self.bomba1.potencia,
                'flow': round(self.bomba1.flujo, 2),
            },
            'pump2':{
                'duty': self.bomba2.potencia,
                'flow': round(self.bomba2.flujo, 2),
            },
            'heater':{
                'duty': self.calentador.potencia,
                'power': round((self.calentador.potencia * 40) / 100, 2),
                'temp1': round(self.calentador.temp1, 2),
                'temp2': round(self.calentador.temp2, 2),
            },
            'valves':{
                'valve1_state': 1 if self.valvulas.state_valve1 else 0,
                'valve2_state': 1 if self.valvulas.state_valve2 else 0,
                'flow1': round(self.valvulas.flow1, 2),
                'flow2': round(self.valvulas.flow2, 2),
            },
            'tank':{
                'level':round(self.estanque.nivel, 1),
                'temp3': round(self.estanque.temp3, 2),
                'temp4': round(self.estanque.temp4, 2),
            },
            'radiator':{
                'duty': self.disipador.potencia,
                'temp5': round(self.disipador.temp5, 2),
                'temp6': round(self.disipador.temp6, 2)
            }
        }
        
        return self.mqtt_dict


    def print_status(self):
        self.update_status()
        print(f"Potencia Bomba1: {self.bomba1.potencia}%")
        print(f"Flujo Bomba1: {self.bomba1.flujo} L/min")
        print(f"Potencia Bomba2: {self.bomba2.potencia}%")
        print(f"Flujo Bomba2: {self.bomba2.flujo} L/min")
        print(f"Potencia Calentador: {self.calentador.potencia}%")
        print(f"Temp 1: {self.calentador.temp1:.2f}°C")
        print(f"Temp 2: {self.calentador.temp2:.2f}°C")
        print(f"Estado Valvula 1: {'Abierta' if self.valvulas.state_valve1 else 'Cerrada'}")
        print(f"Estado Valvula 2: {'Abierta' if self.valvulas.state_valve2 else 'Cerrada'}")
        print(f"Flujo Valvula 1: {self.valvulas.flow1} L/min")
        print(f"Flujo Valvula 2: {self.valvulas.flow2} L/min")
        print(f"Nivel Estanque: {self.estanque.nivel} cm")
        print(f"Temperatura Estanque #3: {self.estanque.temp3:.2f}°C")
        print(f"Temperatura Estanque #4: {self.estanque.temp4:.2f}°C")
    

    def append_to_data_log(self, folder_path="./test_data"):
        """Colecta los datos actuales y los guarda para Excel"""
        self.update_status()

        # Colectar datos reales de los sensores
        data_point = self.update_status_dict()
    
        self.data_log.append(data_point)
        self.log.info(f"Datos colectados: {data_point['Timestamp']} - Total: {len(self.data_log)} puntos")

    def export_to_csv(self, folder_path="./test_data"):
        """Exporta los datos colectados a Excel"""
        if not self.data_log:
            print("No datos para exportar!")
            return
        
        os.makedirs(folder_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"solarloop_test_{timestamp}.csv"
        filepath = os.path.join(folder_path, filename)

        df = pd.DataFrame(self.data_log)
        df.to_csv(filepath, index=False)

        self.log.info(f"Todos los datos exportados: {filepath}")
        print(f"CSV hecho con {len(self.data_log)} datos: {filepath}")
        return filepath
    
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
        === RESUMEN DE DATOS ===
        Total de puntos: {count}
        Primer registro: {first_time}
        Último registro: {last_time}
        ========================
                """
        return summary

if __name__ == "__main__":
    loop = Loop(
        bomba = Bomba(),
        valvulas = Valvulas(),
        calentador = Calentador(),
        estanque = Estanque(),
        disipador=Disipador(),
        verbose= True
    )

    # Limpiar cualquier log anterior de datos
    loop.clear_data_log()

    # Activar componentes necesarios
    loop.set_abrir_valvula(1)              # Abrir válvula 1
    loop.set_potencia_bomba(1, 80)            # Encender bomba al 70%
    loop.set_potencia_calentador(75)       # Encender calentador al 60%

    print("Sistema activado. Iniciando registro de datos por 30 minutos (1 muestra por minuto)...")

    # Guardar el tiempo de inicio
    tiempo_inicio = time.monotonic()
    duracion_total = 1 * 60  # 30 minutos en segundos
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
    loop.export_to_csv()


