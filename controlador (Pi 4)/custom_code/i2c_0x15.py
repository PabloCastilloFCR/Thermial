import smbus2
import time
from cmd_dictionary import cmd_dict

def send_command(PICO_ADDRESS, id, cmd, data=[], verbose = False):
    bus = smbus2.SMBus(1)  # I2C Bus der Raspberry Pi 4
    packet = [id, cmd, len(data)] + data
    bus.write_i2c_block_data(PICO_ADDRESS, 0x00, packet)
    cmd_str = "SET" if cmd == 0x01 else "GET"
    if verbose:
        print(f"Enviado: ADD={PICO_ADDRESS:02x}, CMD={cmd_str}, LEN={len(data)}, DATA={data}")

def receive_response(PICO_ADDRESS, verbose = False):
    try:
        bus = smbus2.SMBus(1)  # I2C Bus der Raspberry Pi 4
        data = bus.read_i2c_block_data(PICO_ADDRESS, 0x00, 8)
        response_id = data[0]
        response_cmd = data[1]
        response_len = data[2]
        response_data = data[3:3+response_len]

        if response_cmd in cmd_dict:
            response_cmd_str = cmd_dict[response_cmd]
        else:
            response_cmd_str = "UNKNOWN"

        if response_cmd == 0x12:  # Temperatur-Wert
            if len(response_data) == 4:
                temp_in_value = response_data[0] + (response_data[1] << 8)
                temp_out_value = response_data[2] + (response_data[3] << 8)
                temp_in_value /= 100.0
                temp_out_value /= 100.0
                if verbose:
                    print(f"Temperatures received: temp_in = {temp_in_value:.2f}°C, temp_out = {temp_out_value:.2f}°C")
                return temp_in_value, temp_out_value
            else:
                print(f"Error: incomplete data, expecting 4 bytes but receiving: {response_len}: {response_data}")
                return None

        if response_cmd == 0x15:  # PWM-Wert des Ventilators
            if len(response_data) == 1:
                pwm_value = response_data[0]
            if verbose:
                print(f"PWM received: {pwm_value}%")
                print(f"Received: ADD={PICO_ADDRESS:02x}, CMD={response_cmd_str}, LEN={response_len}, DATA={pwm_value}")
        return response_id, response_cmd, response_data

    except Exception as e:
        if verbose:
            print(f"Error while reading the answer: {e}")
        return None

if __name__ == "__main__":
    PICO_ADDRESSES = [0x15]  # I2C-Adresse des Ventilator-Moduls
    bus = smbus2.SMBus(1)

    value = 70       # PWM Startwert
    increment = 5  # PWM Schrittgröße

    try:
        while True:
            for pico_add in PICO_ADDRESSES:
                send_command(pico_add, 0, 0x02)  # GET Temperature
                time.sleep(0.5)
                receive_response(pico_add, verbose=True)
                time.sleep(0.5)
                send_command(pico_add, 0, 0x01, [value])  # SET PWM
                time.sleep(1)

            value += increment
            if value > 100 or value < 70:
                increment = -increment
                value += increment

    except KeyboardInterrupt:
        print("Ventilator is turned off")
        for pico_add in PICO_ADDRESSES:
            send_command(pico_add, 0, 0x01, [0], verbose=True)
            time.sleep(0.2) 
        print("Ventilador OFF.")     