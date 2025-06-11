import smbus2
import time
from cmd_dictionary import cmd_dict


def send_command(PICO_ADDRESS, id, cmd, data=[], verbose = False):
    """
    Envía un comando al periferico.
    :param id: ID único del comando. No importa
    :param cmd: Código del comando (1 byte)
    :param data: Datos adicionales (lista de bytes)
    """
    bus = smbus2.SMBus(1)  # Canal I2C en la Raspberry Pi 4
    packet = [id, cmd, len(data)] + data
    bus.write_i2c_block_data(PICO_ADDRESS, 0x00, packet)
    #print(f"Paquete enviado: {packet}")
    cmd_str = "SET" if cmd == 0x01 else "GET" #0x02 GET
    if verbose:
        print(f"Enviado: ADD={PICO_ADDRESS:02x}, CMD={cmd_str}, LEN={len(data)}, DATA={data}")

def receive_response(PICO_ADDRESS, verbose=False)-> float:
    """
    Recibe la respuesta del periferico.
    """

    try:
        bus = smbus2.SMBus(1)  # Canal I2C en la Raspberry Pi 4 para comunicarse con la Rasp. Pi Pico
        data = bus.read_i2c_block_data(PICO_ADDRESS, 0x00, 5) ## <<< Aqui puede estar el error
        if verbose:
            print(f"Datos recibidos sin procesar: {data}") #Debugging
        response_id = data[0]
        response_cmd = data[1]
        response_len = data[2]
        response_data = data[3:3+response_len] #<< Revisar
        
        if response_cmd in cmd_dict:
            response_cmd_str = cmd_dict[response_cmd]
        else:
            response_cmd_str = "UNKNOWN"
        #response_cmd_str = cmd_dict[response_cmd]
    # aquí el valor de flujo se extrae de los datos recibidos
        if response_cmd == 0x13: # cmd para flow, Wenn es sich um die "FLOW"-Antwort handelt
            flow_value = response_data[0] + (response_data[1] << 8) #combina los dos Bytes
            flow_value /= 100.0 #wenn der Wert skaliert wurde, teile durch 100
            if verbose:
                print(f"Flujo recibido: {flow_value:.2f}")#Fliesskommazahl ausgeben
        
        #Ausgabe der gesamt empfangenen Antwort
        if verbose:
            print(f"Recibido: ADD={PICO_ADDRESS:02x}, CMD={response_cmd_str}, LEN={response_len}, DATA={response_data}")
        return flow_value
    except Exception as e:
        print(f"Error al leer la respuesta: {e}")
        return None


if __name__ == "__main__":
    # uC = microcontrolador
    PICO_ADDRESSES = 0x10 #, 0x11, 0x12, 0x13]  # Direcciones I2C de los uC
    bus = smbus2.SMBus(1)  # Canal I2C en la Raspberry Pi 4

    value = 70
    increment = 5

    while True:
        # Enviar comando SET con el valor actual de value 
        send_command(PICO_ADDRESSES, 0, 0x01, [value])
        time.sleep(0.5)

        # Enviar comando GET
        send_command(PICO_ADDRESSES, 0, 0x02)
        time.sleep(0.5)

        # Leer la respuesta del dispositivo
        receive_response(PICO_ADDRESSES) #<< aqui esta fallando. 
        
        time.sleep(0.5)
        # Enviar comando SET con el value = 0
        #send_command(pico_add, 0, 0x01, [0])

    # Incrementar o decrementar el valor de X
    value += increment
    if value > 100 or value < 70:
        increment = -increment  # Cambiar la dirección de incremento
        value += increment  # Ajustar X dentro del rango
