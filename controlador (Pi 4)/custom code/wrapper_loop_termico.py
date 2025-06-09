# --- Imports der Module ---
from modulo_bomba_loop_termico_nuevo import Bomba    
from modulo_valvulas_loop_termico import Valvulas    
from modulo_calentador_loop_termico import Calentador
from modulo_nivel_loop_termico import Nivel
import time


class SolarLoop:
    def __init__(self, bomba: Bomba, valvulas: Valvulas, calentador: Calentador, nivel: Nivel):
        self.bomba = Bomba()
        self.valvulas = Valvulas()
        self.calentador = Calentador()
        self.nivel = Nivel()

    def potencia_bomba(self, potencia):
        self.bomba.set_potencia(potencia)
    
    def get_flujo_bomba(self):
        self.bomba.get_flujo()
    
    def potencia_calentador(self, pwm):
        self.calentador.set_pwm_calentador(pwm)
    
    def temperaturas_calentador(self):
        self.calentador.get_temperaturas()
    
    
# --- Instanzen erstellen ---
bomba = Bomba()
valvulas = Valvulas()
calentador = Calentador()
nivel = Nivel()

# --- Bomba (0x10) ---
def set_potencia_bomba(potencia):
    bomba.set_potencia(potencia) #setear
    print(f"✅ Potencia de la bomba seteada a {potencia}%")

def get_flujo_bomba():
    flujo = bomba.get_flujo() #obtener
    print(f"🌊 Flujo medido (sensor bomba): {flujo} L/min")
    return flujo

# --- Calentador (0x11) ---
def set_pwm_calentador(pwm):
    calentador.set_pwm_calentador(pwm)
    print(f"🔥 PWM del calentador seteado a {pwm}%")

def get_temperaturas_calentador():
    temps = calentador.get_temperaturas()
    if temps is None:
        print("Error al leer temperaturas del calentador")
        return None, None
    t1, t2 = temps
    print(f"Temperaturas calentador: T1 = {t1} °C, T2 = {t2} °C")
    return t1, t2
    

# --- Valvulas (0x12) ---
def abrir_valvula_1():
    valvulas.abrir_valvula(1)
    print("✅ Válvula 1 abierta")

def cerrar_valvula_1():
    valvulas.cerrar_valvula(1)
    print("❌ Válvula 1 cerrada")

def abrir_valvula_2():
    valvulas.abrir_valvula(2)
    print("✅ Válvula 2 abierta")

def cerrar_valvula_2():
    valvulas.cerrar_valvula(2)
    print("❌ Válvula 2 cerrada")

def get_flujos_valvulas():
    flujos = valvulas.get_flujos()
    if flujos is not None:
        f1, f2 = flujos
        print(f"🌊 Flujos válvulas: F1 = {f1} L/min, F2 = {f2} L/min")
    else:
        print("No se pudo leer el flujo de las válvulas.")

# --- Nivel (0x13) ---
def get_nivel():
    nivel_valor = nivel.get_nivel()
    print(f"📏 Nivel actual: {nivel_valor}")
    return nivel_valor

def get_temperaturas_nivel():
    t3, t4 = nivel.get_temperaturas()
    print(f"🌡️ Temperaturas tanque: T3 = {t3} °C, T4 = {t4} °C")
    return t3, t4


if __name__ == "__main__":
   # set_potencia_bomba(100)
   # for i in range (9):    
    #  time.sleep(10)
    #  get_flujo_bomba()
    #  set_potencia_bomba(0)
    #abrir_valvula_1()
    #cerrar_valvula_2()
    #get_flujos_valvulas()
    #set_pwm_calentador(0)
    get_temperaturas_calentador()
    get_nivel()
    get_temperaturas_nivel()
