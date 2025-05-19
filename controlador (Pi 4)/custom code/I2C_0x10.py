import smbus2
import time

cmd_dict = {
    0x12 : "TEMPERATURE",
    0x13 : "FLOW",
    0x14 : "LEVEL"
}

def send_command(PICO_ADDRESS, id, cmd, data=[]):
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
    print(f"Enviado: ADD={PICO_ADDRESS:02x}, CMD={cmd_str}, LEN={len(data)}, DATA={data}")

def receive_response(PICO_ADDRESS):
    """
    Recibe la respuesta del periferico.
    """
    #bus = smbus2.SMBus(1)  # Canal I2C en la Raspberry Pi 4 para comunicarse con la Rasp. Pi Pico
    
    try:
        data = bus.read_i2c_block_data(PICO_ADDRESS, 0x00, 5) ## <<< Aqui puede estar el error
        print(f"Empfangene Rohdaten: {data}") #Debugging
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
            
            print(f"Flujo recibido: {flow_value:.2f}")#Fliesskommazahl ausgeben
        
        #Ausgabe der gesamt empfangenen Antwort
        print(f"Recibido: ADD={PICO_ADDRESS:02x}, CMD={response_cmd_str}, LEN={response_len}, DATA={response_data}")
        return response_id, response_cmd, response_data
    except Exception as e:
        print(f"Error al leer la respuesta: {e}")
        return None


if __name__ == "__main__":
    # uC = microcontrolador
    PICO_ADDRESSES = [0x10] #, 0x11, 0x12, 0x13]  # Direcciones I2C de los uC
    bus = smbus2.SMBus(1)  # Canal I2C en la Raspberry Pi 4

    value = 70
    increment = 5

    while True:
        for pico_add in PICO_ADDRESSES:
            # Enviar comando SET con el valor actual de value 
            send_command(pico_add, 0, 0x01, [value])
            time.sleep(0.5)

            # Enviar comando GET
            send_command(pico_add, 0, 0x02)
            time.sleep(0.5)

            # Leer la respuesta del dispositivo
            receive_response(pico_add) #<< aqui esta fallando. 
            
            time.sleep(0.5)
            # Enviar comando SET con el value = 0
            #send_command(pico_add, 0, 0x01, [0])

        # Incrementar o decrementar el valor de X
        value += increment
        if value > 100 or value < 70:
            increment = -increment  # Cambiar la dirección de incremento
            value += increment  # Ajustar X dentro del rango
