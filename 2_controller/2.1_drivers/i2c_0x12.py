import smbus2
import time
from cmd_dictionary import cmd_dict



def send_command(id, cmd, data=[], verbose = False):
    """
    Sendet einen Befehl an den Pico über I2C.
    :param id: Befehls-ID (kann ignoriert werden)
    :param cmd: Befehlscode (1 Byte)
    :param data: Zusätzliche Daten (Liste von Bytes)
    """
    PICO_ADDRESS = 0x12
    bus = smbus2.SMBus(1)  # I2C-Kanal des Raspberry Pi 4
    packet = [id, cmd, len(data)] + data
    bus.write_i2c_block_data(PICO_ADDRESS, 0x00, packet)
    cmd_str = "SET" if cmd == 0x01 else "GET"
    cmd_str = cmd_dict.get(cmd, "UNKNOWN")
    if verbose:
        print(f"Enviado: ADD={PICO_ADDRESS:02x}, CMD={cmd_str}, LEN={len(data)}, DATA={data}")

def receive_response(address, verbose=False):
    """
    Recibe los datos del Pico y emite los datos del flujo
    """
    PICO_ADDRESS = 0x12
    try:
        bus = smbus2.SMBus(1)
        data = bus.read_i2c_block_data(PICO_ADDRESS, 0x00, 7)  # 6 Bytes erwartet
        #print(f"Datos recibidos (sin procesar): {data}")  # Debugging

        response_cmd = data[0]
        response_len = data[1]
        response_data = data[2:2+response_len]
        print("Raw bytes:", response_data)

        cmd_str = cmd_dict.get(response_cmd, "UNKNOWN")

        if response_cmd == 0x13 and len(response_data) >= 5:  # data del flujo y información estatus válvulas (abierta/cerrada)
            flow1 = response_data[0] + (response_data[1] << 8)
            flow2 = response_data[2] + (response_data[3] << 8)
            valve_status = response_data[4]
            
            flow1 /= 100.0
            flow2 /= 100.0
            #if verbose:
            print(f"Flow 1: {flow1:.2f} L/min, Flow 2: {flow2:.2f} L/min")
            
            valvula1 = "abierta" if valve_status & 0x01 else "cerrada"
            valvula2 = "abierta" if valve_status & 0x02 else "cerrada"
            if verbose:
                print(f"Valvula 1 es {valvula1}, Valvula 2 es {valvula2}")

        if verbose:
            print(f"Respuesta: ADD={PICO_ADDRESS:02x}, CMD={cmd_str}, LEN={response_len}, DATA={response_data}")
        
        return flow1, flow2, valvula1, valvula2

    except Exception as e:
        print(f"Error al leer la respuesta: {e}")
        return None, None, None, None
""" 
Voy a comentar estas funciones porque están fuera de la norma que definimos.

def abrir_valvula1():
     send_command(0, 0x01, [1])
     time.sleep(1)
     receive_response(0)

def cerrar_valvula1():
    send_command(0, 0x01, [3])
    time.sleep(0.1)
    receive_response(0)

def abrir_valvula2():
    send_command(0, 0x01, [2])
    time.sleep(0.1)
    receive_response(0)

def cerrar_valvula2():
    send_command(0, 0x01, [4])
    time.sleep(0.1)
    receive_response(0)
"""
    
if __name__ == "__main__":
    # I2C-Adresse des Pico
    PICO_ADDRESS = 0x12  
    bus = smbus2.SMBus(1)  # I2C-Kanal des Raspberry Pi 4
    
    time.sleep(2)
    #abrir_valvula2()
    #time.sleep(2)
    #leer_flujo()
    #time.sleep(2)
    #cerrar_valvula1()
    #time.sleep(2)
    #cerrar_valvula2()
        
    #while True:
        # Beispiel: Ventil 1 öffnen
        #send_command(0, 0x01, [1])
        #time.sleep(2)

        # Beispiel: Ventil 2 öffnen
        #send_command(0, 0x01, [2])
        #time.sleep(2)

        # Beispiel: Ventil 1 schließen
        #send_command(0, 0x01, [3])
        #time.sleep(2)

        # Beispiel: Ventil 2 schließen
        #send_command(0, 0x01, [4])
        #time.sleep(2)

    #Flow-Daten abrufen:
    send_command(0, 0x02)
    time.sleep(1)
    receive_response(0)
        
        #time.sleep(3)  # Warten, bevor der nächste Zyklus startet
    

        
