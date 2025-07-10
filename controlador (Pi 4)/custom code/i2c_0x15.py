import smbus2
import time
from cmd_dictionary import cmd_dict


def send_command(PICO_ADDRESS, id, cmd, data=[], verbose=False):
    """
    Envía un comando al periferico.
    :param id: ID único del comando. No importa
    :param cmd: Código del comando (1 byte)
    :param data: Datos adicionales (lista de bytes)
    """
    bus = smbus2.SMBus(1)  # Canal I2C en la Raspberry Pi 4
    packet = [id, cmd, len(data)] + data
    bus.write_i2c_block_data(PICO_ADDRESS, 0x00, packet)
    cmd_str = "SET" if cmd == 0x01 else "GET"
    if verbose:
        print(f"Enviado: ADD={PICO_ADDRESS:02x}, CMD={cmd_str}, LEN={len(data)}, DATA={data}")


def receive_response(PICO_ADDRESS, verbose=False) -> float:
    """
    Recibe la respuesta del periferico.
    """
    try:
        fan_speed = None
        bus = smbus2.SMBus(1)
        data = bus.read_i2c_block_data(PICO_ADDRESS, 0x00, 4)  # ID, CMD, LEN=1, DATA
        if verbose:
            print(f"Datos recibidos sin procesar: {data}")
        response_id = data[0]
        response_cmd = data[1]
        response_len = data[2]
        response_data = data[3:3+response_len]

        if response_cmd in cmd_dict:
            response_cmd_str = cmd_dict[response_cmd]
        else:
            response_cmd_str = "UNKNOWN"

        if response_cmd == 0x16:  # cmd para ventilador
            fan_speed = response_data[0]
            if verbose:
                print(f"Velocidad recibida: {fan_speed}%")

        if verbose:
            print(f"Recibido: ADD={PICO_ADDRESS:02x}, CMD={response_cmd_str}, LEN={response_len}, DATA={response_data}")

        return fan_speed

    except Exception as e:
        print(f"Error al leer la respuesta: {e}")
        return None


if __name__ == "__main__":
    # uC = microcontrolador
    PICO_ADDRESSES = 0x15
    bus = smbus2.SMBus(1)

    value = 70
    increment = 5

    while True:
        # Enviar comando SET con el valor actual
        send_command(PICO_ADDRESSES, 0, 0x01, [value])
        time.sleep(0.5)

        # Enviar comando GET
        send_command(PICO_ADDRESSES, 0, 0x02)
        time.sleep(0.5)

        # Leer la respuesta del dispositivo
        receive_response(PICO_ADDRESSES)

        time.sleep(0.5)

        # Incrementar o decrementar el valor
        value += increment
        if value > 100 or value < 70:
            increment = -increment
            value += increment
