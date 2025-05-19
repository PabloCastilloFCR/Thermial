import smbus2
import time

cmd_dict = {
    0x12 : "TEMPERATURE",
    0x13 : "FLOW",
    0x14 : "LEVEL" 
}

def send_command(PICO_ADDRESS, id, cmd, data=[]):
    """
    Envía un comando al esclavo.
    :param id: ID único del comando
    :param cmd: Código del comando (1 byte)
    :param data: Datos adicionales (lista de bytes)
    """
    bus = smbus2.SMBus(1)  # Canal I2C en la Raspberry Pi 4
    packet = [id, cmd, len(data)] + data
    bus.write_i2c_block_data(PICO_ADDRESS, 0x00, packet)
    #print(f"Paquete enviado: {packet}")
    cmd_str = "SET" if cmd == 0x01 else "GET"
    print(f"Enviado: ADD={PICO_ADDRESS:02x}, CMD={cmd_str}, LEN={len(data)}, DATA={data}")

def receive_response(PICO_ADDRESS):
    """
    Recibe la respuesta del esclavo.
    """
    bus = smbus2.SMBus(1)  # Canal I2C en la Raspberry Pi 4

    try:
        data = bus.read_i2c_block_data(PICO_ADDRESS, 0x00, 4)
        response_id = data[0]
        response_cmd = data[1]
        response_len = data[2]
        response_data = data[3:3+response_len]

        response_cmd_str = cmd_dict[response_cmd]

        print(f"Recibido: ADD={PICO_ADDRESS:02x}, CMD={response_cmd_str}, LEN={response_len}, DATA={response_data}")
        return response_id, response_cmd, response_data
    except Exception as e:
        print(f"Error al leer la respuesta: {e}")
        return None


if __name__ == "__main__":
    # uC = microcontrolador
    PICO_ADDRESSES = [0x10, 0x11, 0x12, 0x13]  # Direcciones I2C de los uC
    bus = smbus2.SMBus(1)  # Canal I2C en la Raspberry Pi 4

    value = 0
    increment = 10

    while True:
        for pico_add in PICO_ADDRESSES:
            # Enviar comando SET con el valor actual de X
            send_command(pico_add, 0, 0x01, [value])
            time.sleep(0.5)

            # Enviar comando GET
            send_command(pico_add, 0, 0x02)
            time.sleep(0.5)

            # Leer la respuesta del dispositivo
            receive_response(pico_add)

            send_command(pico_add, 0, 0x01, [0])

        # Incrementar o decrementar el valor de X
        value += increment
        if value > 100 or value < 0:
            increment = -increment  # Cambiar la dirección de incremento
            value += increment  # Ajustar X dentro del rango
