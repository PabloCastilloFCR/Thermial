# --- Imports der Module ---
import logging
from modulo_bomba_loop_termico_nuevo import Bomba    
from modulo_valvulas_loop_termico import Valvulas    
from modulo_calentador_loop_termico import Calentador
from modulo_nivel_loop_termico import Estanque
import time

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
        self.log.info("Calentador seteado a %.0f W", pwm * 40)
    
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
        self.log.info("Temperaturas estanque: T1=%.2f °C, T2=%.2f °C", t3, t4)

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


if __name__ == "__main__":
    loop = SolarLoop(
        bomba = Bomba(),
        valvulas = Valvulas(),
        calentador = Calentador(),
        estanque = Estanque(),
        verbose= True
    )

    loop.log.info("Prueba 1: Abrir Valvula 1. Encender Bomba 10 segundos. Apagar todo.")
    time.sleep(3)
    loop.abrir_valvula(1)
    time.sleep(1)
    loop.potencia_bomba(100)
    time.sleep(1)
    loop.print_status()
    time.sleep(10)
    loop.stop()
    time.sleep(1)
    loop.print_status()
