# --- Imports der Module ---
from modulo_bomba_flujo import Bomba    
from modulo_valvulas_loop_termico import Valvulas    
from modulo_calentador_loop_termico import Calentador
from modulo_nivel_loop_termico import Nivel

# --- Instanzen erstellen ---
bomba = Bomba()
valvulas = Valvulas()
calentador = Calentador()
nivel = Nivel()

# --- Bomba (0x10) ---
def setear_potencia_bomba(potencia):
    bomba.setear_potencia(potencia)
    print(f"✅ Potencia de la bomba seteada a {potencia}%")

def obtener_flujo_bomba():
    flujo = bomba.obtener_flujo()
    print(f"🌊 Flujo medido (sensor bomba): {flujo} L/min")
    return flujo

# --- Calentador (0x11) ---
def setear_pwm_calentador(pwm):
    calentador.setear_pwm(pwm)
    print(f"🔥 PWM del calentador seteado a {pwm}%")

def obtener_temperaturas_calentador():
    t1, t2 = calentador.obtener_temperaturas()
    print(f"🌡️ Temperaturas calentador: T1 = {t1} °C, T2 = {t2} °C")
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

def obtener_flujos_valvulas():
    f1, f2 = valvulas.leer_flujos()
    print(f"🌊 Flujos válvulas: F1 = {f1} L/min, F2 = {f2} L/min")
    return f1, f2

# --- Nivel (0x13) ---
def obtener_nivel():
    nivel_valor = nivel.obtener_nivel()
    print(f"📏 Nivel actual: {nivel_valor} %")
    return nivel_valor

def obtener_temperaturas_nivel():
    t3, t4 = nivel.obtener_temperaturas()
    print(f"🌡️ Temperaturas tanque: T3 = {t3} °C, T4 = {t4} °C")
    return t3, t4


if __name__ == "__main__":
    setear_potencia_bomba(80)
    obtener_flujo_bomba()
    abrir_valvula_1()
    cerrar_valvula_2()
    obtener_flujos_valvulas()
    setear_pwm_calentador(50)
    obtener_temperaturas_calentador()
    obtener_nivel()
    obtener_temperaturas_nivel()