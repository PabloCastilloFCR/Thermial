import smbus2
import time
from cmd_dictionary import cmd_dict

def send_command(PICO_ADDRESS, id, cmd, data=[], verbose=False):
    bus = smbus2.SMBus(1)
    packet = [id, cmd, len(data)] + data
    bus.write_i2c_block_data(PICO_ADDRESS, 0x00, packet)
    cmd_str = "SET" if cmd == 0x01 else "GET"
    if verbose:
        print(f"Enviado: ADD={PICO_ADDRESS:02x}, CMD={cmd_str}, LEN={len(data)}, DATA={data}")

def receive_response(PICO_ADDRESS, verbose=False) -> float:
    try:
        bus = smbus2.SMBus(1)
        data = bus.read_i2c_block_data(PICO_ADDRESS, 0x00, 5)
        if verbose:
            print(f"Datos recibidos sin procesar: {data}")
        response_id = data[0]
        response_cmd = data[1]
        response_len = data[2]
        response_data = data[3:3+response_len]
        if verbose:
            print("Raw bytes:", response_data)

        if response_cmd in cmd_dict:
            response_cmd_str = cmd_dict[response_cmd]
        else:
            response_cmd_str = "UNKNOWN"

        if response_cmd == 0x13:  # FLOW-Response
            flow_value = response_data[0] + (response_data[1] << 8)
            flow_value /= 100.0

        if verbose:
            print(f"Flujo recibido: {flow_value:.2f}")
            print(f"Recibido: ADD={PICO_ADDRESS:02x}, CMD={response_cmd_str}, LEN={response_len}, DATA={response_data}")
        return flow_value

    except Exception as e:
        print(f"Error al leer la respuesta: {e}")
        return None


if __name__ == "__main__":
    PICO_ADDRESSES = 0x10
    bus = smbus2.SMBus(1)

    # Werte für Stresstest
    values_to_test = [70, 75, 80, 85, 90, 95, 100]
    cycles = 100  # wie oft die Sequenz wiederholt wird
    verbose = True

    for cycle in range(cycles):
        print(f"\n--- Cycle {cycle+1}/{cycles} ---")
        for value in values_to_test:
            try:
                # SET-Befehl
                send_command(PICO_ADDRESSES, 0, 0x01, [value], verbose=verbose)
                time.sleep(0.05)  # minimale Pause, um I2C nicht komplett zu blockieren

                # GET-Befehl
                send_command(PICO_ADDRESSES, 0, 0x02, verbose=verbose)
                time.sleep(0.05)

                # Response lesen
                resp = receive_response(PICO_ADDRESSES, verbose=verbose)
                if resp is None:
                    print(f"Warnung: Keine Antwort bei Wert {value}")

            except Exception as e:
                print(f"Fehler bei Wert {value}: {e}")

    # Am Ende alles auf 0 setzen
    send_command(PICO_ADDRESSES, 0, 0x01, [0], verbose=True)
    time.sleep(0.5)
    print("Stresstest beendet, alle Werte auf 0 gesetzt.")
